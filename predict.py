import sys
from zenml import pipeline
from mlflow import MlflowClient
from scripts.entity.exception import AppException
from scripts.steps.inference import yolov8_prediction
from scripts.config.configuration import ConfigurationManager


@pipeline
def prediction():
    config = ConfigurationManager()
    eval = config.get_evaluation()
    uri = config.get_train_log_config()
    client = MlflowClient(tracking_uri=uri.mlflow_uri)

    if not eval.version is None:
        model_version = client.get_model_version(name=eval.name, version=eval.version) 
        run_id = model_version.run_id

        #get the artifact source
        run_info = client.get_run(run_id)
        artifact_uri = run_info.info.artifact_uri.replace("mlflow-artifacts:", "mlartifacts")
        model = f"{artifact_uri}/model/artifacts/best.pt"

        yolov8_prediction(model_path=model,
                            image_source=eval.data_source,
                            save_path = eval.save_dir,
                            model_name = eval.name)
    else:
        model_versions = client.search_model_versions(f"name = '{eval.name}'")

        production_run_id = None
        for version in model_versions:
            if version.current_stage == "Production":
                production_run_id = version.run_id
                break

        run_info = client.get_run(production_run_id)
        artifact_uri = run_info.info.artifact_uri.replace("mlflow-artifacts:", "mlartifacts")
        model = f"{artifact_uri}/model/artifacts/best.pt"

        yolov8_prediction(model_path=model,
                            image_source=eval.data_source,
                            save_path = eval.save_dir,
                            model_name = eval.name)



if __name__ == "__main__":
    try:
        prediction()
    except Exception as e:
        raise AppException(e, sys)
    