# Cron Log Processor Script for MOR Explorer

## How to run:
1) Create a `.env` file with fields:
```angular2html
RPC_URL=
ETHERSCAN_API_KEY=
SLACK_URL=
SPREADSHEET_ID=
```

2) Place `google-sheet-credentials-example.json` in the `sheet_config` directory

3) `pip install -r "requirements.txt"`

### Flow
1) `cron_master_processor.py` calls `scripts/`
- `i_update_user_claim_locked_events.py`
- `ii_update_user_multipliers.py`
- `iii_update_total_daily_rewards.py`

2) `i_update_user_claim_locked_events.py` fetches the latest `UserClaimLocked` events
from the blockchain and populates the google sheet with that data for
`UserClaimLocked` sub-sheet/worksheet.
3) `ii_update_user_multipliers.py` fetches the `UserClaimLocked` worksheet and fetches the multipliers
for each address in an async fashion using the async provider and uploads to 
the `UserMultiplier` worksheet.
4) `iii_update_total_daily_rewards.py`fetches the `UserMultiplier` worksheet and for each address, it
calculates the Daily and Total Staked Rewards using the `getCurrentUserReward` ABI function and then
uploads the results to the `RewardSum` worksheet.

### Details

1) Uses batch processing, async web3 provider, async code and retries for any rate limits
```angular2html:
from web3 import AsyncWeb3

w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(ETH_RPC_URL))
```

NOTE: This project uses sheet utils and slack notification