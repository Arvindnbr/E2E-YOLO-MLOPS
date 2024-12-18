from zenml import step, ArtifactConfig
from zenml.logger import get_logger
import os,sys, yaml
from scripts.utils.log import logger
from scripts.entity.exception import AppException
from scripts.utils.common import update_train_yaml
from scripts.config.configuration import DataIngestionConfig
from typing import Annotated, Tuple
from zenml import save_artifact

logger = get_logger(__name__)


class DataValidation:
    def __init__(self, config: DataIngestionConfig, current_path: str):
        self.config = config
        self.current_path = current_path

    def validate_labels(self, path):
        train_labels = f"{path}/train/labels"
        valid_labels = f"{path}/valid/labels"
        #test_labels = f"{path}/test/labels"
        
        with open(f"{path}/data.yaml", 'r') as y:
            yaml_dump = yaml.safe_load(y)
        
        num_classes = int(yaml_dump['nc'])-1
        corrupted = []
        for i in [train_labels, valid_labels,]:
            for file in os.listdir(i):
                if file.endswith('.txt'):
                    with open(os.path.join(i,file), 'r') as f:
                        for line in f.readlines():
                            part = line.strip().split()
                            if int(part[0]) > num_classes:
                                corrupted.append(file)
        return corrupted
    
    def validate_img(self, path):
        train_images_path = os.path.join(path,"train/images")
        valid_images_path = os.path.join(path,"valid/images")
        train_images = []
        valid_images = []

        for i in os.listdir(train_images_path):
            if i.endswith('.jpg') or i.endswith('.png') or i.endswith('.jpeg'):
                train_images.append(i)
        for i in os.listdir(valid_images_path):
            if i.endswith('.jpg') or i.endswith('.png') or i.endswith('.jpeg'):
                valid_images.append(i)

        train_labels = os.listdir(os.path.join(path,"train/labels"))
        valid_labels = os.listdir(os.path.join(path,"valid/labels"))
        if len(train_images) == len(train_labels) and len(valid_images) == len(valid_labels):
            return True
        else: 
            return False


    def validate_files(self, current_path)-> bool:
        try:
            validation_status = None
            validation_path = f"{self.config.unzip_dir}/data_validation"
            all_files = os.listdir(current_path)
            os.makedirs(validation_path, exist_ok=True)
            status_file = f"{validation_path}/status.txt"
            for file in all_files:
                if file not in ['train', 'valid', 'test', 'data.yaml']:
                    validation_status = False
                    with open(status_file,'w') as f:
                        f.write(f"validation status: {validation_status}")
                    
                else:
                    corrupted = self.validate_labels(current_path)
                    val_status = self.validate_img(current_path)

                    if val_status == False:
                        print("Images and labels mismatch - unequal label and images")
                        validation_status = False
                        with open(status_file,'w') as f:
                            f.write(f"validation status: {validation_status}")
                    
                    elif len(corrupted) > 0:
                        print(f"labels out of index / corrupted labels : {corrupted}")
                        validation_status = False
                        with open(status_file,'w') as f:
                            f.write(f"validation status: {validation_status}")
                    else:
                        validation_status = True
                        with open(status_file, 'w') as f:
                            f.write(f"validation_status: {validation_status}")
            print(all_files,"\nValidated successfully")
            return validation_status
        except Exception as e:
            raise AppException(e,sys)
        
    def update_yaml(self, current_path):
        yamlpath = os.path.join(current_path,"data.yaml")
        update_train_yaml(yamlpath,current_path)
        logger.info(f"following changes has been made \n train and valid path inside data.yaml has been modified \n path : {current_path} has been added to data.yaml file ")

    


@step(enable_cache=False)
def validator(config:DataIngestionConfig, dir:str)->Tuple[Annotated[bool, "validation status"],
                                                           Annotated[str, ArtifactConfig(name="Dataset_path",is_model_artifact=True)]]:
    try:
        validator = DataValidation(config, dir)
        status = validator.validate_files(dir)
        validator.update_yaml(dir)
        save_artifact(dir, name = f"current_dataset_path : {dir}")
        return status, dir
    except Exception as e:
        raise AppException(e,sys)

















    