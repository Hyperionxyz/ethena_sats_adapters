import logging
import subprocess
import json
from typing import Dict, List, Optional
import requests

from dotenv import load_dotenv
from constants.summary_columns import SummaryColumn
from constants.example_integrations import (
    HYPERION_SUSDE_START_BLOCK,
)
from constants.hyperion import (
    HYPERION_ADDRESS_API_URL,
    HYPERION_DEX_ADDRESS,
    SUSDE_ADDRESS
)
from constants.chains import Chain
from integrations.integration_ids import IntegrationID as IntID
from integrations.l2_delegation_integration import L2DelegationIntegration

load_dotenv()


class HyperionAptosIntegration(L2DelegationIntegration):
    def __init__(
        self,
        integration_id: IntID,
        start_block: int,
        token_address: str,
        decimals: int,
        chain: Chain = Chain.APTOS,
        reward_multiplier: int = 1,
    ):
        super().__init__(
            integration_id=integration_id,
            start_block=start_block,
            chain=chain,
            summary_cols=[SummaryColumn.HYPERION_SHARDS],
            reward_multiplier=reward_multiplier,
        )
        self.token_address = token_address
        self.decimals = str(decimals)
        self.hyperion_ts_location = "ts/hyperion_balances.ts"

    def get_l2_block_balances(
        self, cached_data: Dict[int, Dict[str, float]], blocks: List[int]
    ) -> Dict[int, Dict[str, float]]:
        logging.info("Getting block data for hyperion sUSDe LP...")
        # Ensure blocks are sorted smallest to largest
        block_data: Dict[int, Dict[str, float]] = {}
        sorted_blocks = sorted(blocks)

        # Populate block data from smallest to largest
        for block in sorted_blocks:
            user_addresses = self.get_hyperion_block_participants(block)

            result = self.get_hyperion_block_data(block, user_addresses)

            # Store the balances and cache the exchange rate
            if result:
                block_data[block] = result

        return block_data

    def get_hyperion_block_participants(self, block: int) -> any:
        try:
            response = requests.get(
                f"{HYPERION_ADDRESS_API_URL}?block={block}", timeout=10
            )
            response.raise_for_status()

            data = response.json()
            if not isinstance(data, list):
                logging.warning(f"Unexpected response format from API: {data}")
                return []

            return data

        except requests.RequestException as e:
            logging.error(f"Request failed for block {block}: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Error processing participants for block {block}: {str(e)}")
            return []

    def get_hyperion_block_data(
        self, block: int, user_addresses: any
    ):
        print("Getting participants data for block: ", block)
        if not user_addresses:
            user_addresses = []
        try:
            response = subprocess.run(
                [
                    "ts-node",
                    self.hyperion_ts_location,
                    HYPERION_DEX_ADDRESS,
                    str(self.decimals),
                    str(block),
                    json.dumps(user_addresses),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            try:
                result = json.loads(response.stdout)
                return result
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                print(f"Raw output: {response.stdout}")
                raise

        except subprocess.CalledProcessError as e:
            print(f"Process error: {e}")
            print(f"stderr: {e.stderr}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise


if __name__ == "__main__":
    example_integration = HyperionAptosIntegration(
        integration_id=IntID.HYPERION_SUSDE_LP,
        start_block=HYPERION_SUSDE_START_BLOCK,
        token_address=SUSDE_ADDRESS,
        decimals=6,
        chain=Chain.APTOS,
        reward_multiplier=5,
    )

    example_integration_output = example_integration.get_l2_block_balances(
        cached_data={},
        blocks=list(range(HYPERION_SUSDE_START_BLOCK, HYPERION_SUSDE_START_BLOCK + 15306000, 1500000)),
    )

    print("=" * 120)
    print("Run without cached data", example_integration_output)
    print("=" * 120, "\n" * 5)
