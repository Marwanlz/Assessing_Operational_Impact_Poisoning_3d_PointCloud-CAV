# Impact analysis of data poisoning on GAN-based data augmentation techniques

## Paper
This repository contains the code and datasets associated with the following paper:
**Assessing the Operational Impact of Poisoning Attacks over Augmented 3D Point Cloud Public Datasets for Connected and Autonomous Vehicles**

Marwan Lazrag, Badis Hammi, Lorena Gonzalez-Manzano, Joaquin Garcia-Alfaro

SECRYPT 2026

## Main resources contained in this repository

### 1. Impact Assessment Tool

Source code available at the [operational-impact-assessment folder](./operational-impact-assessment/) 

Follow the instructions below.

#### Install Docker et Docker-Compose

#### Build the docker image

sudo docker build -t bia .

#### Start the service

sudo docker-compose up

#### Test the tool

Open a web browser and go to http://127.0.0.1:8003 to access its GUI

### 2. Datasets and classification process

Open and process the following two files 

[Classification.ipynb](./datasets-and-classification-process/Classification.ipynb)

[process_data.py](./datasets-and-classification-process/process_data.py)

## Acknowledgements:
* Impact Assessment tool: The impact assessment tool used in this work is based on our previous work, [the Business Impact Analyser](https://gitlab.com/tsp-soccrates-components/bia).
* Datasets and classification process : The data augmentation and classification process is based on these two projects: [3DGAN](https://github.com/xchhuang/simple-pytorch-3dgan/) and [InceptionNet](https://github.com/fgn02/Advanced-Image-Classification-through-CNNs), with modifications including parameter adjustments and a new function to generate .mat objects as output to train the 3D-GAN and produce new synthetic 3D point clouds.

## References

If using this code for research purposes, please cite:

M. Lazrag, B. Hammi, L. Gonzalez-Manzano, J. Garcia-Alfaro. Assessing the Operational Impact of Poisoning Attacks over Augmented 3D Point Cloud Public Datasets for Connected and Autonomous Vehicles. Proceedings of the 23rd International Conference on Security and Cryptography (SECRYPT 2026), Porto, Portugal, 16-18 July 2026.

```
@inproceedings{lazrag2026secrypt,
  title={{Assessing the Operational Impact of Poisoning Attacks over Augmented 3D Point Cloud Public Datasets for Connected and Autonomous Vehicles}},
  author={Lazrag, Marwan and Hammi, Badis, and Gonzalez-Manzano, Lorena and Garcia-Alfaro, Joaquin},
  booktitle={Proceedings of the 23rd International Conference on Security and Cryptography (Secrypt 2026), Porto, Portugal},
  isbn={},
  issn={},
  pages={},
  month={July},
  year={2026},
  doi = {},
  url = {},
}
```
