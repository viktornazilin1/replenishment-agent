from ai_core_sdk.ai_core_v2_client import AICoreV2Client

def get_ai_core_client():
    return AICoreV2Client(
        base_url="https://api.ai.prod.eu-central-1.aws.ml.hana.ondemand.com/v2",
        auth_url="https://ch-btp-crossapplications-aws-m1l0l74s.authentication.eu10.hana.ondemand.com/oauth/token",
        client_id="sb-f19f4d8c-b05e-4b27-be8d-078b16184a01!b319508|aicore!b540",
        client_secret="5313e6f5-f6ff-49c9-a35f-deafd68bec92$HBrwBydTZUai0iY3fySLUBEnF3yZ7rkvhXzChq5oO3I="
    )