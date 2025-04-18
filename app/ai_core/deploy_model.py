from app.ai_core.client import get_ai_core_client

def deploy_model():
    client = get_ai_core_client()

    # Шаг 1. Создание сценария (model definition)
    scenario_payload = {
        "name": "xgboost-forecasting",
        "description": "Serve XGBoost model via AI Core SDK",
        "input": {
            "type": "openapi",
            "openapi": {
                "request": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "instances": {
                                    "type": "array",
                                    "items": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "output": {
            "type": "openapi"
        }
    }

    scenario = client.scenario.create(scenario_payload)
    print("✅ Scenario создан:", scenario.get("name"))

    # Шаг 2. Создание деплоя
    deployment_payload = {
        "name": "xgboost-forecasting-deployment",
        "scenarioName": "xgboost-forecasting",
        "deploymentConfigurationName": "default",
        "runtime": {
            "image": "docker.io/<your-docker-user>/xgboost-forecasting:latest",  # 👈 замени на свой!
            "entrypoint": {
                "command": ["python"],
                "args": ["serve.py"]
            },
            "ports": [{"containerPort": 8080}]
        }
    }

    deployment = client.deployment.create(deployment_payload)
    print("✅ Deployment создан:", deployment.get("name"))

if __name__ == "__main__":
    deploy_model()
