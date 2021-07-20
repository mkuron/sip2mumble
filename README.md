A SIP gateway for Mumble. It uses PyMumble (by Robert Hendrickx) to connect to a Mumble server and Shtoom (by Anthony Baxter) to talk to a SIP user agent.
Shtoom was discontinued in 2005, but is the only Python SIP library that can do audio with PCM buffers.

If the SIP user agent calls the gateway, it appears as a user on the Mumble server and a voice connection to the root channel is established.
If the SIP user agent registers with the gateway (not implemented yet), it rings when a global message is received. Upon picking up the phone, a voice connection to the root channel is established.
