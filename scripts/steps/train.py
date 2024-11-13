import os, sys
import logging
import torch
from scripts.entity.exception import AppException
from scripts.config.configuration import *
from ultralytics import YOLO, settings
from zenml import step
from zenml.logger import get_logger
from zenml.types import CSVString
from scripts.materializer.yolo_materializer import UltralyticsMaterializer
from scripts.utils.common import start_tensorboard
import pandas as pd
from typing import Annotated, Any, Dict, Tuple
from ultralytics import YOLO
from zenml import ArtifactConfig, step, log_artifact_metadata
from scripts.utils.common import early_stopping_callback


logger = get_logger(__name__)





class ModelTrainer:
    def __init__(self, config: TrainLogConfig, val: DataIngestionConfig, param: Params):
        self.config = config
        self.param = param
        self.val = val

    def validation_status(self, status):
        status_file = f"{self.val.unzip_dir}/data_validation/status.txt"
        with open(status_file, 'r') as file:
            status = file.read().strip()
        key, value = status.split(':')
        key = key.strip()
        value = value.strip()

        if key != "validation_status":
            raise ValueError("unexpected key in status file")
        
        if value == 'True':
            if value == status:
                return True
        elif value == 'False':
            return False
        else:
            raise ValueError("validation status is invalid")
        

    def train_model(self, current_dset, yolo_model):

        settings.update({'mlflow': True})
        settings.reset()
        project_dir = f"{self.config.runs_root}/{self.config.experiment_name}"
        
        dataset_dir = current_dset
        data_path = os.path.join( dataset_dir, "data.yaml")
        logging.info(f"Dataset location: {data_path}")
        if torch.cuda.is_available():
            device = torch.cuda.current_device()
            logging.info(f"Device is running on: {torch.cuda.get_device_name(device)}")
        else:
            logging.info(f"CUDA is not available")
            device = "cpu"
            logging.info(f"Device to run on: {device}")
            logging.info(data_path)
            logging.info(f"saving runs to {project_dir}/{self.config.model_name}. ---------- Logging into tensorboard")

        model = yolo_model
        project_root = f"{project_dir}/{self.config.model_name}"
        start_tensorboard(logdir=project_root,
                          port=6010)
        trained = model.train(
                data=data_path,
                optimizer = self.param.optimizer,
                lr0 = self.param.lr0,
                save_period = self.param.save_period,
                batch = self.param.batch,
                epochs = self.param.epochs,
                resume = self.param.resume,
                seed = self.param.seed,
                imgsz = self.param.imgsz,
                project = project_dir,
                name = self.config.model_name,
                patience = self.param.patience,
                cache = self.param.cache,
                workers = self.param.workers,
                cos_lr = self.param.cos_lr,
                close_mosaic = self.param.close_mosaic,
                amp = self.param.amp,
                lrf = self.param.lrf,
                momentum = self.param.momentum,
                weight_decay = self.param.weight_decay,
                warmup_epochs = self.param.warmup_epochs,
                warmup_momentum = self.param.warmup_momentum,
                warmup_bias_lr = self.param.warmup_bias_lr,
                box = self.param.box,
                cls = self.param.cls,    
                hsv_h = self.param.hsv_h,             
                hsv_s = self.param.hsv_s,                 
                hsv_v = self.param.hsv_v,
                degrees = self.param.degrees,   
                translate = self.param.translate,
                scale = self.param.scale,
                shear = self.param.shear,  
                perspective = self.param.perspective, 
                flipud = self.param.flipud,
                fliplr = self.param.fliplr,
                bgr = self.param.bgr,
                mosaic = self.param.mosaic,     
                mixup = self.param.mixup,
                copy_paste = self.param.copy_paste,  
                auto_augment = self.param.auto_augment,
                erasing = self.param.erasing,
                crop_fraction = self.param.crop_fraction,
                freeze = self.param.freeze,
                exist_ok = True)
    
        return trained
    
    def resume_train(self, trained_model):
        settings.update({'mlflow': True})
        settings.reset()

        model = trained_model

        data_path = model.ckpt['train_args']['data']
        logging.info(f"Dataset location: {data_path}")

        project_root = model.ckpt["train_args"]["save_dir"]
        start_tensorboard(logdir=project_root,
                          port=6010)

        if os.path.exists(data_path):

            if torch.cuda.is_available():
                device = torch.cuda.current_device()
                logging.info(f"Device is running on: {torch.cuda.get_device_name(device)}")
            else:
                logging.info(f"CUDA is not available")
                device = "cpu"
                logging.info(f"Device to run on: {device}")
                logging.info(f"Model path {model.ckpt_path}")

            trained = model.train(
                    data=data_path,
                    optimizer = self.param.optimizer,
                    lr0 = self.param.lr0,
                    save_period = self.param.save_period,
                    batch = self.param.batch,
                    epochs = self.param.epochs,
                    resume = self.param.resume,
                    seed = self.param.seed,
                    imgsz = self.param.imgsz,
                    patience = self.param.patience,
                    cache = self.param.cache,
                    workers = self.param.workers,
                    cos_lr = self.param.cos_lr,
                    close_mosaic = self.param.close_mosaic,
                    amp = self.param.amp,
                    lrf = self.param.lrf,
                    momentum = self.param.momentum,
                    weight_decay = self.param.weight_decay,
                    warmup_epochs = self.param.warmup_epochs,
                    warmup_momentum = self.param.warmup_momentum,
                    warmup_bias_lr = self.param.warmup_bias_lr,
                    box = self.param.box,
                    cls = self.param.cls,    
                    hsv_h = self.param.hsv_h,             
                    hsv_s = self.param.hsv_s,                 
                    hsv_v = self.param.hsv_v,
                    degrees = self.param.degrees,   
                    translate = self.param.translate,
                    scale = self.param.scale,
                    shear = self.param.shear,  
                    perspective = self.param.perspective, 
                    flipud = self.param.flipud,
                    fliplr = self.param.fliplr,
                    bgr = self.param.bgr,
                    mosaic = self.param.mosaic,     
                    mixup = self.param.mixup,
                    copy_paste = self.param.copy_paste,  
                    auto_augment = self.param.auto_augment,
                    erasing = self.param.erasing,
                    crop_fraction = self.param.crop_fraction,
                    freeze = self.param.freeze,
                    )
        
            return trained
        else:
            logging.info(f"{data_path} doesnot exists......\nkindly check the path and run again")
            exit(1)


        


@step(enable_cache=True, enable_step_logs=True)
def load_model(model_checkpoint: str,
               ) -> Annotated[YOLO, ArtifactConfig(name="Raw_YOLO", is_model_artifact=True)]:
    logger.info(f"Loading YOLO checkpoint {model_checkpoint}")
    YOLOModel = YOLO(model_checkpoint)
    YOLOModel.add_callback('on_val_epoch_end', early_stopping_callback)
    return YOLOModel   

@step(output_materializers={"Trained_YOLO": UltralyticsMaterializer},
      enable_cache=False,
      )
def Trainer(config:TrainLogConfig,val_config: DataIngestionConfig,
            params:Params,validation_status: bool,current_dset: str,
            yolo_model: YOLO) -> Tuple[Annotated[YOLO, ArtifactConfig(name="Trained_YOLO", is_model_artifact=True)],
                                       Annotated[Dict[str, Any], "validation_metrics"],
                                       Annotated[Dict[str, Any], "model_names"],
                                       Annotated[str, "Model metrics"],
                                       Annotated[CSVString, "Table"]]:
    try:
        trainer = ModelTrainer(config,val_config,params)
        trainer.validation_status(validation_status)
        trained = trainer.train_model(current_dset, yolo_model)

        save_dir = str(trained.save_dir)
        log_artifact_metadata(artifact_name="Trained_YOLO",metadata={"metrics": trained.results_dict, "names": yolo_model.names, "Save directory": save_dir},)
        df = pd.read_csv(f"{save_dir}/results.csv")
        csv_string = df.to_csv(index=True)
        return yolo_model, trained.results_dict, yolo_model.names,save_dir, CSVString(csv_string)
    except Exception as e:
        raise AppException(e, sys)
    


@step(output_materializers={"Trained_YOLO": UltralyticsMaterializer},
      enable_cache=False,
      )
def ResumeTrain(config:TrainLogConfig,val_config: DataIngestionConfig,
            params:Params,yolo_model: YOLO) -> Tuple[Annotated[YOLO, ArtifactConfig(name="Trained_YOLO", is_model_artifact=True)],
                                       Annotated[Dict[str, Any], "validation_metrics"],
                                       Annotated[Dict[str, Any], "model_names"],
                                       Annotated[str, "Model metrics"],
                                       Annotated[CSVString, "Table"]]:   
    
    try:
        trainer = ModelTrainer(config,val_config,params)
        trained = trainer.resume_train(yolo_model)

        save_dir = str(trained.save_dir)
        log_artifact_metadata(artifact_name="Trained_YOLO",metadata={"metrics": trained.results_dict, "names": yolo_model.names, "Save directory": save_dir},)
        df = pd.read_csv(f"{save_dir}/results.csv")
        csv_string = df.to_csv(index=True)
        return yolo_model, trained.results_dict, yolo_model.names,save_dir, CSVString(csv_string)
    except Exception as e:
        raise AppException(e, sys)