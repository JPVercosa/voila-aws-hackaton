from strands.models import BedrockModel

NOVA_MODEL = BedrockModel(
    model_id="amazon.nova-pro-v1:0",
    region_name="us-east-1",
    temperature=0.2,
    top_p=0.9,
)