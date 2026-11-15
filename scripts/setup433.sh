set -x
cd /tmp
for i in 1 2 3 4 5; do
  curl -sSL -C - -m 900 -o lean433.tar.zst "https://github.com/leanprover/lean4/releases/download/v4.33.0-rc1/lean-4.33.0-rc1-linux.tar.zst" && sz=$(stat -c%s lean433.tar.zst) && echo "size=$sz" && [ "$sz" -gt 300000000 ] && break
  sleep 5
done
python3 - <<'PY'
import zstandard, tarfile
d=zstandard.ZstdDecompressor()
with open('/tmp/lean433.tar.zst','rb') as f:
    with d.stream_reader(f) as r:
        with tarfile.open(fileobj=r, mode='r|') as t:
            t.extractall('/tmp/lean433', filter='data')
print("extracted")
PY
mkdir -p /home/user/.elan/toolchains
rm -rf "/home/user/.elan/toolchains/leanprover--lean4---v4.33.0-rc1"
mv /tmp/lean433/lean-4.33.0-rc1-linux "/home/user/.elan/toolchains/leanprover--lean4---v4.33.0-rc1"
/home/user/.elan/toolchains/leanprover--lean4---v4.33.0-rc1/bin/lean --version
if [ ! -d /opt/lean-lib/mathlib4-433 ]; then
  git clone --depth 1 --branch v4.33.0-rc1 https://github.com/leanprover-community/mathlib4 /opt/lean-lib/mathlib4-433 || exit 1
fi
cat /opt/lean-lib/mathlib4-433/lean-toolchain
cd /opt/lean-lib/mathlib4-433
export ELAN_HOME=/home/user/.elan
export PATH=$ELAN_HOME/bin:$PATH
for i in 1 2 3; do lake exe cache get && break; sleep 5; done
echo "SETUP433_DONE"
