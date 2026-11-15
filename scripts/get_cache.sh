set -x
export ELAN_HOME=/home/user/.elan
export PATH=$ELAN_HOME/bin:$PATH
cd /opt/lean-lib/mathlib4
cat lean-toolchain
lake --version || exit 1
for i in 1 2 3; do lake exe cache get && break; sleep 5; done
echo "CACHE_DONE"
