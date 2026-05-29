#!/bin/bash
# webtool_deploy.sh

cd "$(dirname "$0")"  # cron

logfile="logs/$(date +"%Y%m%d_%H%M%S")_deploy.log"
exec > >(tee -a "$logfile") 2>&1

echo "Current working directory: $(pwd)"

# conda environment
source /home/bpeng/anaconda3/etc/profile.d/conda.sh
conda activate crop-server

# ─── Configuration ────────────────────────────────────────────────────────────
YEAR=$(date +"%Y")
TODAY_DOY=$(date +"%j" | sed 's/^0*//')

# test only
# TODAY_DOY=${1:-$(date +"%j" | sed 's/^0*//')} 

SCHEDULED_DAYS=(140 156 172 188 204 220 236 252 268 284)
CROPS=("corn" "soybean")

BNN_BASE="/home/bpeng/NIFA_BNN/BNN/result"
REPO_DIR="/home/bpeng/cyber-agricultural-system"
PUBLIC_BASE="${REPO_DIR}/public/20260306"
# ──────────────────────────────────────────────────────────────────────────────

echo "==================== Deploy started: $(date +"%Y-%m-%d %H:%M:%S") ===================="

# ─── Step 1: 确认今天是调度日 ─────────────────────────────────────────────────
MATCHED_DOY=""
for D in "${SCHEDULED_DAYS[@]}"; do
  if [ "$TODAY_DOY" -eq "$D" ]; then
    MATCHED_DOY=$D
    break
  fi
done

if [ -z "$MATCHED_DOY" ]; then
  echo "[deploy] DOY ${TODAY_DOY} is not available for deployment, exit..."
  exit 0
fi

echo "[deploy] ===== DOY=${MATCHED_DOY}, YEAR=${YEAR} ====="

# ─── Step 2: 复制结果文件到repo ───────────────────────────────────────────────
for CROP in "${CROPS[@]}"; do
  SRC_DIR="${BNN_BASE}/${CROP}/bnn_${MATCHED_DOY}"
  DST_DIR="${PUBLIC_BASE}/result_${CROP}/bnn_${MATCHED_DOY}"

  FILE_MAIN="result_test_${YEAR}_doy${MATCHED_DOY}.csv"
  FILE_WITH_STATE="result_test_${YEAR}_doy${MATCHED_DOY}_with_state_county.csv"

  # 等待结果文件生成（最多30分钟）
  WAITED=0
  echo "[deploy] Waiting ${SRC_DIR}/${FILE_MAIN} ..."
  until [ -f "${SRC_DIR}/${FILE_MAIN}" ]; do
    sleep 60
    WAITED=$((WAITED + 60))
    if [ $WAITED -ge 1800 ]; then
      echo "[deploy] Run out of time: ${CROP} DOY${MATCHED_DOY} skipped..."
      continue 2
    fi
  done

  mkdir -p "$DST_DIR"
  cp "${SRC_DIR}/${FILE_MAIN}"       "${DST_DIR}/${FILE_MAIN}"
  cp "${SRC_DIR}/${FILE_WITH_STATE}" "${DST_DIR}/${FILE_WITH_STATE}"
  echo "[deploy] ✓ successful ${CROP} DOY${MATCHED_DOY}"
done

# ─── Step 3: Build + Deploy到GitHub Pages ────────────────────────────────────
echo "[deploy] npm run deploy..."

cd "$REPO_DIR"
npm run deploy

echo "==================== Deploy completed: $(date +"%Y-%m-%d %H:%M:%S") ===================="
