from zenml import pipeline
import os
from scripts.entity.exception import AppException
from scripts.steps.ingestion import data_ingest
from scripts.steps.sorting import data_sort
from scripts.steps.validation import validator
from scripts.steps.train import Trainer, load_model
from scripts.steps.log_mlflow import register_model
from scripts.config.configuration import ConfigurationManager
from scripts.entity.entity import DataIngestionConfig, DataSetConfig, DataValidationConfig, TrainLogConfig, Params, TresholdMetrics
from scripts.steps.best_model import production_model
from typing import Annotated, Any, Dict, Tuple
import logging
from ultralytics import YOLO
from zenml import ArtifactConfig, step, log_artifact_metadata



@pipeline
def data_pipeline(config: DataIngestionConfig, 
                  dset_config: DataSetConfig, 
                  val_config: DataValidationConfig,
                  trainlog_config: TrainLogConfig, 
                  parameters: Params,
                  threshold: TresholdMetrics
                  )->Tuple[Annotated[str, ArtifactConfig(name="Production_YOLO_model", is_model_artifact=True)],
                           Annotated[str, ArtifactConfig(name="Dataset",is_model_artifact=True)]]:
    
    datapath = data_ingest(config)
    print(datapath)

    if len(dset_config.classes) != 0:
        current_dset = data_sort(dset_config, datapath)
        print(current_dset)
    else:
        current_dset = datapath
        print(current_dset)
    
    dset = current_dset
    status, dir = validator(val_config,dset)
    logging.info(f"status:{status} and current_dset: {dset}")
    yolo_model = load_model(trainlog_config.model)
    yolo_model, metrics, names, save_dir = Trainer(config=trainlog_config,
                                                   val_config=val_config,
                                                   params=parameters,
                                                   validation_status=status,
                                                   current_dset=current_dset,
                                                   yolo_model=yolo_model
                                                   )                                            
    os.environ["MLFLOW_TRACKING_URI"] = trainlog_config.mlflow_uri
    run_id, experiment_id = register_model(experiment_name = trainlog_config.experiment_name,
                                           model_name = trainlog_config.model_name,
                                           save_dir = save_dir
                                           )
    name, version, model = production_model(run_id, threshold)
    return model, dset



    
    