set -x
export ELAN_HOME=/home/user/.elan
curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -o /tmp/elan-init.sh || exit 1
sh /tmp/elan-init.sh -y --default-toolchain none || exit 1
export PATH=$ELAN_HOME/bin:$PATH
sudo mkdir -p /opt/lean-lib
sudo chown -R user:user /opt/lean-lib
if [ ! -d /opt/lean-lib/mathlib4 ]; then
  git clone --depth 1 https://github.com/leanprover-community/mathlib4 /opt/lean-lib/mathlib4 || exit 1
fi
cd /opt/lean-lib/mathlib4
cat lean-toolchain
TOOL=$(cat lean-toolchain)
elan toolchain install "$TOOL" || exit 1
lake exe cache get
echo "SETUP_DONE"
