# Copyright (c) 2023, Oracle and/or its affiliates.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2.0, as
# published by the Free Software Foundation.
#
# This program is also distributed with certain software (including
# but not limited to OpenSSL) that is licensed under separate terms,
# as designated in a particular file or component or in included license
# documentation.  The authors of MySQL hereby grant you an
# additional permission to link the program and your derivative works
# with the separately licensed software that they have included with
# MySQL.
#
# Without limiting anything contained in the foregoing, this file,
# which is part of MySQL Connector/Python, is also subject to the
# Universal FOSS Exception, version 1.0, a copy of which can be found at
# http://oss.oracle.com/licenses/universal-foss-exception.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License, version 2.0, for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA

"""LDAP SASL Authentication Plugin."""

import hmac

from base64 import b64decode, b64encode
from hashlib import sha1, sha256
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple
from uuid import uuid4

from ..authentication import ERR_STATUS
from ..errors import InterfaceError, ProgrammingError
from ..logger import logger
from ..types import StrOrBytes

if TYPE_CHECKING:
    from ..network import MySQLSocket

try:
    import gssapi
except ImportError:
    raise ProgrammingError(
        "Module gssapi is required for GSSAPI authentication "
        "mechanism but was not found. Unable to authenticate "
        "with the server"
    ) from None

from ..utils import (
    normalize_unicode_string as norm_ustr,
    validate_normalized_unicode_string as valid_norm,
)
from . import MySQLAuthPlugin

AUTHENTICATION_PLUGIN_CLASS = "MySQLLdapSaslPasswordAuthPlugin"


# pylint: disable=c-extension-no-member,no-member
class MySQLLdapSaslPasswordAuthPlugin(MySQLAuthPlugin):
    """Class implementing the MySQL ldap sasl authentication plugin.

    The MySQL's ldap sasl authentication plugin support two authentication
    methods SCRAM-SHA-1 and GSSAPI (using Kerberos). This implementation only
    support SCRAM-SHA-1 and SCRAM-SHA-256.

    SCRAM-SHA-1 amd SCRAM-SHA-256
        This method requires 2 messages from client and 2 responses from
        server.

        The first message from client will be generated by prepare_password(),
        after receive the response from the server, it is required that this
        response is passed back to auth_continue() which will return the
        second message from the client. After send this second message to the
        server, the second server respond needs to be passed to auth_finalize()
        to finish the authentication process.
    """

    sasl_mechanisms: List[str] = ["SCRAM-SHA-1", "SCRAM-SHA-256", "GSSAPI"]
    def_digest_mode: Callable = sha1
    client_nonce: Optional[str] = None
    client_salt: Any = None
    server_salt: Optional[str] = None
    krb_service_principal: Optional[str] = None
    iterations: int = 0
    server_auth_var: Optional[str] = None
    target_name: Optional[gssapi.Name] = None
    ctx: gssapi.SecurityContext = None
    servers_first: Optional[str] = None
    server_nonce: Optional[str] = None

    @staticmethod
    def _xor(bytes1: bytes, bytes2: bytes) -> bytes:
        return bytes([b1 ^ b2 for b1, b2 in zip(bytes1, bytes2)])

    def _hmac(self, password: bytes, salt: bytes) -> bytes:
        digest_maker = hmac.new(password, salt, self.def_digest_mode)
        return digest_maker.digest()

    def _hi(self, password: str, salt: bytes, count: int) -> bytes:
        """Prepares Hi
        Hi(password, salt, iterations) where Hi(p,s,i) is defined as
        PBKDF2 (HMAC, p, s, i, output length of H).
        """
        pw = password.encode()
        hi = self._hmac(pw, salt + b"\x00\x00\x00\x01")
        aux = hi
        for _ in range(count - 1):
            aux = self._hmac(pw, aux)
            hi = self._xor(hi, aux)
        return hi

    @staticmethod
    def _normalize(string: str) -> str:
        norm_str = norm_ustr(string)
        broken_rule = valid_norm(norm_str)
        if broken_rule is not None:
            raise InterfaceError(f"broken_rule: {broken_rule}")
        return norm_str

    def _first_message(self) -> bytes:
        """This method generates the first message to the server to start the

        The client-first message consists of a gs2-header,
        the desired username, and a randomly generated client nonce cnonce.

        The first message from the server has the form:
            b'n,a=<user_name>,n=<user_name>,r=<client_nonce>

        Returns client's first message
        """
        cfm_fprnat = "n,a={user_name},n={user_name},r={client_nonce}"
        self.client_nonce = str(uuid4()).replace("-", "")
        cfm: StrOrBytes = cfm_fprnat.format(
            user_name=self._normalize(self._username),
            client_nonce=self.client_nonce,
        )

        if isinstance(cfm, str):
            cfm = cfm.encode("utf8")
        return cfm

    def _first_message_krb(self) -> Optional[bytes]:
        """Get a TGT Authentication request and initiates security context.

        This method will contact the Kerberos KDC in order of obtain a TGT.
        """
        user_name = gssapi.raw.names.import_name(
            self._username.encode("utf8"), name_type=gssapi.NameType.user
        )

        # Use defaults store = {'ccache': 'FILE:/tmp/krb5cc_1000'}#,
        #                       'keytab':'/etc/some.keytab' }
        # Attempt to retrieve credential from default cache file.
        try:
            cred: Any = gssapi.Credentials()
            logger.debug(
                "# Stored credentials found, if password was given it will be ignored."
            )
            try:
                # validate credentials has not expired.
                cred.lifetime
            except gssapi.raw.exceptions.ExpiredCredentialsError as err:
                logger.warning(" Credentials has expired: %s", err)
                cred.acquire(user_name)
                raise InterfaceError(f"Credentials has expired: {err}") from err
        except gssapi.raw.misc.GSSError as err:
            if not self._password:
                raise InterfaceError(
                    f"Unable to retrieve stored credentials error: {err}"
                ) from err
            try:
                logger.debug("# Attempt to retrieve credentials with given password")
                acquire_cred_result = gssapi.raw.acquire_cred_with_password(
                    user_name,
                    self._password.encode("utf8"),
                    usage="initiate",
                )
                cred = acquire_cred_result[0]
            except gssapi.raw.misc.GSSError as err2:
                raise ProgrammingError(
                    f"Unable to retrieve credentials with the given password: {err2}"
                ) from err

        flags_l = (
            gssapi.RequirementFlag.mutual_authentication,
            gssapi.RequirementFlag.extended_error,
            gssapi.RequirementFlag.delegate_to_peer,
        )

        if self.krb_service_principal:
            service_principal = self.krb_service_principal
        else:
            service_principal = "ldap/ldapauth"
        logger.debug("# service principal: %s", service_principal)
        servk = gssapi.Name(
            service_principal, name_type=gssapi.NameType.kerberos_principal
        )
        self.target_name = servk
        self.ctx = gssapi.SecurityContext(
            name=servk, creds=cred, flags=sum(flags_l), usage="initiate"
        )

        try:
            # step() returns bytes | None, see documentation,
            # so this method could return a NULL payload.
            # ref: https://pythongssapi.github.io/<suffix>
            # suffix: python-gssapi/latest/gssapi.html#gssapi.sec_contexts.SecurityContext
            initial_client_token = self.ctx.step()
        except gssapi.raw.misc.GSSError as err:
            raise InterfaceError(f"Unable to initiate security context: {err}") from err

        logger.debug("# initial client token: %s", initial_client_token)
        return initial_client_token

    def auth_continue_krb(
        self, tgt_auth_challenge: Optional[bytes]
    ) -> Tuple[Optional[bytes], bool]:
        """Continue with the Kerberos TGT service request.

        With the TGT authentication service given response generate a TGT
        service request. This method must be invoked sequentially (in a loop)
        until the security context is completed and an empty response needs to
        be send to acknowledge the server.

        Args:
            tgt_auth_challenge the challenge for the negotiation.

        Returns: tuple (bytearray TGS service request,
                        bool True if context is completed otherwise False).
        """
        logger.debug("tgt_auth challenge: %s", tgt_auth_challenge)

        resp = self.ctx.step(tgt_auth_challenge)
        logger.debug("# context step response: %s", resp)
        logger.debug("# context completed?: %s", self.ctx.complete)

        return resp, self.ctx.complete

    def auth_accept_close_handshake(self, message: bytes) -> bytes:
        """Accept handshake and generate closing handshake message for server.

        This method verifies the server authenticity from the given message
        and included signature and generates the closing handshake for the
        server.

        When this method is invoked the security context is already established
        and the client and server can send GSSAPI formated secure messages.

        To finish the authentication handshake the server sends a message
        with the security layer availability and the maximum buffer size.

        Since the connector only uses the GSSAPI authentication mechanism to
        authenticate the user with the server, the server will verify clients
        message signature and terminate the GSSAPI authentication and send two
        messages; an authentication acceptance b'\x01\x00\x00\x08\x01' and a
        OK packet (that must be received after sent the returned message from
        this method).

        Args:
            message a wrapped hssapi message from the server.

        Returns: bytearray closing handshake message to be send to the server.
        """
        if not self.ctx.complete:
            raise ProgrammingError("Security context is not completed.")
        logger.debug("# servers message: %s", message)
        logger.debug("# GSSAPI flags in use: %s", self.ctx.actual_flags)
        try:
            unwraped = self.ctx.unwrap(message)
            logger.debug("# unwraped: %s", unwraped)
        except gssapi.raw.exceptions.BadMICError as err:
            raise InterfaceError(f"Unable to unwrap server message: {err}") from err

        logger.debug("# unwrapped server message: %s", unwraped)
        # The message contents for the clients closing message:
        #   - security level 1 byte, must be always 1.
        #   - conciliated buffer size 3 bytes, without importance as no
        #     further GSSAPI messages will be sends.
        response = bytearray(b"\x01\x00\x00\00")
        # Closing handshake must not be encrypted.
        logger.debug("# message response: %s", response)
        wraped = self.ctx.wrap(response, encrypt=False)
        logger.debug(
            "# wrapped message response: %s, length: %d",
            wraped[0],
            len(wraped[0]),
        )

        return wraped.message

    def auth_response(
        self,
        auth_data: bytes,
        **kwargs: Any,
    ) -> Optional[bytes]:
        """This method will prepare the fist message to the server.

        Returns bytes to send to the server as the first message.
        """
        # pylint: disable=attribute-defined-outside-init
        self._auth_data = auth_data

        auth_mechanism = self._auth_data.decode()
        logger.debug("read_method_name_from_server: %s", auth_mechanism)
        if auth_mechanism not in self.sasl_mechanisms:
            auth_mechanisms = '", "'.join(self.sasl_mechanisms[:-1])
            raise InterfaceError(
                f'The sasl authentication method "{auth_mechanism}" requested '
                f'from the server is not supported. Only "{auth_mechanisms}" '
                f'and "{self.sasl_mechanisms[-1]}" are supported'
            )

        if b"GSSAPI" in self._auth_data:
            return self._first_message_krb()

        if self._auth_data == b"SCRAM-SHA-256":
            self.def_digest_mode = sha256

        return self._first_message()

    def _second_message(self) -> bytes:
        """This method generates the second message to the server

        Second message consist on the concatenation of the client and the
        server nonce, and cproof.

        c=<n,a=<user_name>>,r=<server_nonce>,p=<client_proof>
        where:
            <client_proof>: xor(<client_key>, <client_signature>)

            <client_key>: hmac(salted_password, b"Client Key")
            <client_signature>: hmac(<stored_key>, <auth_msg>)
            <stored_key>: h(<client_key>)
            <auth_msg>: <client_first_no_header>,<servers_first>,
                        c=<client_header>,r=<server_nonce>
            <client_first_no_header>: n=<username>r=<client_nonce>
        """
        if not self._auth_data:
            raise InterfaceError("Missing authentication data (seed)")

        passw = self._normalize(self._password)
        salted_password = self._hi(passw, b64decode(self.server_salt), self.iterations)
        logger.debug("salted_password: %s", b64encode(salted_password).decode())

        client_key = self._hmac(salted_password, b"Client Key")
        logger.debug("client_key: %s", b64encode(client_key).decode())

        stored_key = self.def_digest_mode(client_key).digest()
        logger.debug("stored_key: %s", b64encode(stored_key).decode())

        server_key = self._hmac(salted_password, b"Server Key")
        logger.debug("server_key: %s", b64encode(server_key).decode())

        client_first_no_header = ",".join(
            [
                f"n={self._normalize(self._username)}",
                f"r={self.client_nonce}",
            ]
        )
        logger.debug("client_first_no_header: %s", client_first_no_header)

        client_header = b64encode(
            f"n,a={self._normalize(self._username)},".encode()
        ).decode()

        auth_msg = ",".join(
            [
                client_first_no_header,
                self.servers_first,
                f"c={client_header}",
                f"r={self.server_nonce}",
            ]
        )
        logger.debug("auth_msg: %s", auth_msg)

        client_signature = self._hmac(stored_key, auth_msg.encode())
        logger.debug("client_signature: %s", b64encode(client_signature).decode())

        client_proof = self._xor(client_key, client_signature)
        logger.debug("client_proof: %s", b64encode(client_proof).decode())

        self.server_auth_var = b64encode(
            self._hmac(server_key, auth_msg.encode())
        ).decode()
        logger.debug("server_auth_var: %s", self.server_auth_var)

        msg = ",".join(
            [
                f"c={client_header}",
                f"r={self.server_nonce}",
                f"p={b64encode(client_proof).decode()}",
            ]
        )
        logger.debug("second_message: %s", msg)
        return msg.encode()

    def _validate_first_reponse(self, servers_first: bytes) -> None:
        """Validates first message from the server.

        Extracts the server's salt and iterations from the servers 1st response.
        First message from the server is in the form:
            <server_salt>,i=<iterations>
        """
        if not servers_first or not isinstance(servers_first, (bytearray, bytes)):
            raise InterfaceError(f"Unexpected server message: {repr(servers_first)}")
        try:
            servers_first_str = servers_first.decode()
            self.servers_first = servers_first_str
            r_server_nonce, s_salt, i_counter = servers_first_str.split(",")
        except ValueError:
            raise InterfaceError(
                f"Unexpected server message: {servers_first_str}"
            ) from None
        if (
            not r_server_nonce.startswith("r=")
            or not s_salt.startswith("s=")
            or not i_counter.startswith("i=")
        ):
            raise InterfaceError(
                f"Incomplete reponse from the server: {servers_first_str}"
            )
        if self.client_nonce in r_server_nonce:
            self.server_nonce = r_server_nonce[2:]
            logger.debug("server_nonce: %s", self.server_nonce)
        else:
            raise InterfaceError(
                "Unable to authenticate response: response not well formed "
                f"{servers_first_str}"
            )
        self.server_salt = s_salt[2:]
        logger.debug(
            "server_salt: %s length: %s",
            self.server_salt,
            len(self.server_salt),
        )
        try:
            i_counter = i_counter[2:]
            logger.debug("iterations: %s", i_counter)
            self.iterations = int(i_counter)
        except Exception as err:
            raise InterfaceError(
                f"Unable to authenticate: iterations not found {servers_first_str}"
            ) from err

    def auth_continue(self, servers_first_response: bytes) -> bytes:
        """return the second message from the client.

        Returns bytes to send to the server as the second message.
        """
        self._validate_first_reponse(servers_first_response)
        return self._second_message()

    def _validate_second_reponse(self, servers_second: bytearray) -> bool:
        """Validates second message from the server.

        The client and the server prove to each other they have the same Auth
        variable.

        The second message from the server consist of the server's proof:
            server_proof = HMAC(<server_key>, <auth_msg>)
            where:
                <server_key>: hmac(<salted_password>, b"Server Key")
                <auth_msg>: <client_first_no_header>,<servers_first>,
                            c=<client_header>,r=<server_nonce>

        Our server_proof must be equal to the Auth variable send on this second
        response.
        """
        if (
            not servers_second
            or not isinstance(servers_second, bytearray)
            or len(servers_second) <= 2
            or not servers_second.startswith(b"v=")
        ):
            raise InterfaceError("The server's proof is not well formated")
        server_var = servers_second[2:].decode()
        logger.debug("server auth variable: %s", server_var)
        return self.server_auth_var == server_var

    def auth_finalize(self, servers_second_response: bytearray) -> bool:
        """finalize the authentication process.

        Raises InterfaceError if the ervers_second_response is invalid.

        Returns True in successful authentication False otherwise.
        """
        if not self._validate_second_reponse(servers_second_response):
            raise InterfaceError(
                "Authentication failed: Unable to proof server identity"
            )
        return True

    @property
    def name(self) -> str:
        """Plugin official name."""
        return "authentication_ldap_sasl_client"

    @property
    def requires_ssl(self) -> bool:
        """Signals whether or not SSL is required."""
        return False

    def auth_switch_response(
        self, sock: "MySQLSocket", auth_data: bytes, **kwargs: Any
    ) -> bytes:
        """Handles server's `auth switch request` response.

        Args:
            sock: Pointer to the socket connection.
            auth_data: Plugin provided data (extracted from a packet
                representing an `auth switch request` response).
            kwargs: Custom configuration to be passed to the auth plugin
                when invoked. The parameters defined here will override the ones
                defined in the auth plugin itself.

        Returns:
            packet: Last server's response after back-and-forth
                communication.
        """
        logger.debug("# auth_data: %s", auth_data)
        self.krb_service_principal = kwargs.get("krb_service_principal")

        response = self.auth_response(auth_data, **kwargs)
        if response is None:
            raise InterfaceError("Got a NULL auth response")

        logger.debug("# request: %s size: %s", response, len(response))
        sock.send(response)

        packet = sock.recv()
        logger.debug("# server response packet: %s", packet)

        if len(packet) >= 6 and packet[5] == 114 and packet[6] == 61:  # 'r' and '='
            # Continue with sasl authentication
            dec_response = packet[5:]
            cresponse = self.auth_continue(dec_response)
            sock.send(cresponse)
            packet = sock.recv()
            if packet[5] == 118 and packet[6] == 61:  # 'v' and '='
                if self.auth_finalize(packet[5:]):
                    # receive packed OK
                    packet = sock.recv()
        elif auth_data == b"GSSAPI" and packet[4] != ERR_STATUS:
            rcode_size = 5  # header size for the response status code.
            logger.debug("# Continue with sasl GSSAPI authentication")
            logger.debug("# response header: %s", packet[: rcode_size + 1])
            logger.debug("# response size: %s", len(packet))

            logger.debug("# Negotiate a service request")
            complete = False
            tries = 0  # To avoid a infinite loop attempt no more than feedback messages
            while not complete and tries < 5:
                logger.debug("%s Attempt %s %s", "-" * 20, tries + 1, "-" * 20)
                logger.debug("<< server response: %s", packet)
                logger.debug("# response code: %s", packet[: rcode_size + 1])
                step, complete = self.auth_continue_krb(packet[rcode_size:])
                logger.debug(" >> response to server: %s", step)
                sock.send(step or b"")
                packet = sock.recv()
                tries += 1
            if not complete:
                raise InterfaceError(
                    f"Unable to fulfill server request after {tries} "
                    f"attempts. Last server response: {packet}"
                )
            logger.debug(
                " last GSSAPI response from server: %s length: %d",
                packet,
                len(packet),
            )
            last_step = self.auth_accept_close_handshake(packet[rcode_size:])
            logger.debug(
                " >> last response to server: %s length: %d",
                last_step,
                len(last_step),
            )
            sock.send(last_step)
            # Receive final handshake from server
            packet = sock.recv()
            logger.debug("<< final handshake from server: %s", packet)

            # receive OK packet from server.
            packet = sock.recv()
            logger.debug("<< ok packet from server: %s", packet)

        return bytes(packet)


# pylint: enable=c-extension-no-member,no-member
