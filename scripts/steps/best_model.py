from typing import Annotated, Tuple
import mlflow
import logging
from zenml import step, ArtifactConfig
from dataclasses import asdict
from zenml.logger import get_logger
from scripts.config.configuration import TresholdMetrics


logger = get_logger(__name__)


class ProductionModel:
    def __init__(self) -> None:
        self.client = mlflow.tracking.MlflowClient()

    def get_registered_model_name_from_run(self,run_id: str) -> str:
        registered_models = self.client.search_registered_models()

        for model in registered_models:
            for version in model.latest_versions:
                if version.run_id == run_id:
                    logging.info(f"{model.name} is registered under {run_id}")
                    return model.name
                    
        return None

    def list_models_and_versions(self, name=None):
        if name:
            registered_models = self.client.search_registered_models(filter_string="name LIKE '%'")
        
        models_info = {}

        for model in registered_models:
            model_name = model.name
            models_info[model_name] = []

            versions = model.latest_versions
            
            for version in versions:
                version_info = {
                    "version": version.version,
                    "run_id": version.run_id,
                    "source": version.source
                }
                models_info[model_name].append(version_info)

        logging.info("model info has been fetched")
        return models_info

    def get_model_metrics(self, run_id):
        
        run_data = self.client.get_run(run_id).data.to_dictionary()
        metrics = {
            "mAP50": run_data['metrics'].get('mAP50'),
            "mAP50_95": run_data['metrics'].get('mAP50-95'),
            # "recall": run_data['metrics'].get('recall'),
            # "precision": run_data['metrics'].get('precision')
        }
        logging.info(f"metrics of {run_id} has been retrieved")
        return metrics
    


    
    

@step   
def production_model(run_id: str,
                     thresholds:TresholdMetrics) -> Tuple[Annotated[str, "Production model"],
                                                          Annotated[int, "version"],
                                                          Annotated[str, ArtifactConfig(name="Production_YOLO", is_model_artifact=True)]]:

    client = mlflow.tracking.MlflowClient()
    prod = ProductionModel()
    name = prod.get_registered_model_name_from_run(run_id=run_id)
    models_info = prod.list_models_and_versions(name)

    run_data_dict = client.get_run(run_id).data.to_dictionary()
    map95 = run_data_dict['metrics']['mAP50-95']
    map50 = run_data_dict['metrics']['mAP50']

    if map95>=thresholds.mAP50_95 and map50>=thresholds.mAP50:
        if name not in models_info:
            return "Model not found."
            
        best_run_id = None
        best_metrics = None
        best_version = None
        
        for version_info in models_info[name]:
            run_id = version_info['run_id']
            metrics = prod.get_model_metrics(run_id)

            threshold_dict = asdict(thresholds)
                
            if all(metrics[metric] >= threshold_dict[metric] for metric in threshold_dict):
                if best_metrics is None or (
                    metrics['mAP50_95'] > best_metrics['mAP50_95'] or
                    (metrics['mAP50_95'] == best_metrics['mAP50_95'] and metrics['mAP50'] > best_metrics['mAP50'])
                ):
                    best_run_id = run_id
                    best_metrics = metrics
                    best_version = int(version_info['version'])
                    artifact = version_info['source']
                    artifact = artifact.replace("mlflow-artifacts:", "mlartifacts")
                    model = f"{artifact}/artifacts/best.pt"
            else:
                best_version = int(version_info['version'])
                artifact = version_info['source']
                artifact = artifact.replace("mlflow-artifacts:", "mlartifacts")
                model = f"{artifact}/artifacts/best.pt"
                    
                    
            
        if best_run_id is not None:
            print(f"Best version: {best_version}")
            print(f"Best run ID: {best_run_id}")
            print(f"Best metrics: {best_metrics}")
            print(f"artifact: {artifact}/artifacts/best.pt")
            
            client.transition_model_version_stage(
                name=name,
                version=best_version,
                stage="Production",
                archive_existing_versions=True  # Optional: Archives previous versions in Production
            )
            logging.info(f"{name} model with version{best_version} has been set to production")
            return name, best_version, model
        else:
            logging.info("models failed to meet the threshold, initiate retrain")
            logging.info("No models meet the threshold criteria. kindly update parameters and retrian")
    else:
        logging.info("No models meet the threshold criteria. kindly update parameters and retrian")
        exit(1)