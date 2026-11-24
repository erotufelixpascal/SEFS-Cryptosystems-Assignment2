"""Command-line interface for demonstrations and interoperability testing.

Run from the folder that holds (or will hold) passwd, master.key, masterlist,
*.meta and chunks/:

    python -m sefs keygen
    python -m sefs register alice01
    python -m sefs encrypt report -u alice01
    python -m sefs read report 1019 10 -u alice01

Passwords are prompted for (not echoed) unless given with -p, which is only
meant for scripted demos with throwaway accounts.
"""

import argparse
import getpass
import sys

import sefs


def _pw(args, prompt="Password: "):
    return args.password if args.password is not None else getpass.getpass(prompt)


def _result(r) -> int:
    print("OKAY (1)" if r == sefs.OK else "ERROR (-1)")
    return 0 if r == sefs.OK else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m sefs", description="Secure Encrypted File System")
    sub = ap.add_subparsers(dest="cmd", required=True)

    k = sub.add_parser("keygen", help="create master.key (16-byte key + 16-byte IV)")
    k.add_argument("path", nargs="?", default=sefs.config.MASTER_KEY_FILE)
    k.add_argument("--force", action="store_true", help="overwrite an existing key")

    def user_cmd(name, help_, *extra, needs_user_flag=True):
        sp = sub.add_parser(name, help=help_)
        for e in extra:
            sp.add_argument(e)
        if needs_user_flag:
            sp.add_argument("-u", "--user", required=True)
        sp.add_argument("-p", "--password")
        return sp

    for name, help_ in [("register", "register a user"), ("delete-user", "delete a user"),
                        ("login", "check a username and password")]:
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("user")
        sp.add_argument("-p", "--password")
    sp = sub.add_parser("exists", help="is the username registered?")
    sp.add_argument("user")
    sp = sub.add_parser("passwd", help="change a user's password")
    sp.add_argument("user")
    sp.add_argument("-p", "--password")
    sp.add_argument("-n", "--new-password")

    user_cmd("create", "create an empty SEFS file", "file")
    user_cmd("encrypt", "encrypt a plaintext file on disk into SEFS", "file")
    user_cmd("decrypt", "decrypt a SEFS file to a plaintext file", "file", "out")
    user_cmd("read", "print LEN bytes from POS", "file", "pos", "len")
    user_cmd("write", "insert TEXT at POS", "file", "pos", "text")
    user_cmd("size", "print the file size", "file")
    user_cmd("check", "integrity-check one file", "file")
    user_cmd("delete", "delete a SEFS file", "file")
    user_cmd("health", "integrity-check every file")

    a = ap.parse_args(argv)
    P = sefs.config.PASSWD_FILE

    if a.cmd == "keygen":
        r = sefs.generate_master_key(a.path, overwrite=a.force)
        if r != sefs.OK:
            print(f"{a.path} exists (use --force to replace it) or cannot be written", file=sys.stderr)
        return _result(r)
    if a.cmd == "register":
        return _result(sefs.register_user(a.user, _pw(a), P))
    if a.cmd == "delete-user":
        return _result(sefs.delete_user(a.user, _pw(a), P))
    if a.cmd == "login":
        return _result(sefs.match_user(a.user, _pw(a), P))
    if a.cmd == "exists":
        return _result(sefs.is_user_valid(a.user, P))
    if a.cmd == "passwd":
        old = _pw(a, "Old password: ")
        new = a.new_password if a.new_password is not None else getpass.getpass("New password: ")
        return _result(sefs.change_user_password(a.user, old, new, P))

    u, p = a.user, _pw(a)
    if a.cmd == "create":
        return _result(sefs.create_file(a.file, u, p))
    if a.cmd == "encrypt":
        return _result(sefs.encrypt_file(a.file, u, p))
    if a.cmd == "decrypt":
        return _result(sefs.decrypt_file(a.file, a.out, u, p))
    if a.cmd == "read":
        data = sefs.read_from_file(a.file, int(a.pos), int(a.len), u, p)
        if data is None:
            return _result(sefs.ERR)
        sys.stdout.buffer.write(data + b"\n")
        return 0
    if a.cmd == "write":
        return _result(sefs.write_to_file(a.file, int(a.pos), a.text.encode(), u, p))
    if a.cmd == "size":
        n = sefs.file_size(a.file, u, p)
        print(n)
        return 0 if n >= 0 else 1
    if a.cmd == "check":
        return _result(sefs.file_integrity_check(a.file, u, p))
    if a.cmd == "delete":
        return _result(sefs.delete_file(a.file, u, p))
    if a.cmd == "health":
        return _result(sefs.system_health_check(u, p))
    return 2


if __name__ == "__main__":
    sys.exit(main())
