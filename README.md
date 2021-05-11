# Investigation into FANet for Real-Time Image Semantic Segmentation in Autonomous Driving

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/goromal/FANet_Evaluation/main?filepath=fanet_eval_main.ipynb)

## Source File List

- [airsim_dataset_creation](airsim_dataset_creation.ipynb): Script used to create the AirSim segmentation dataset.
- [fanet_eval_main](fanet_eval_main.ipynb): Script used to validate the speed and performance of the base FANet implementation.
- ...

## Installation and Usage

1. Make sure your Google Drive has plenty of space for this repository.
2. Preview the file [fanet_eval_main.ipynb](fanet_eval_main.ipynb) and other top-level python notebooks and click the link "Open in Colab," which will copy the file to your Google Drive.
3. Follow the Setup steps in the notebook, which will clone the repo and set up all necessary packages.

## Explanation

Image Semantic Segmentation, which allows for object-level reasoning and analysis from either disjoint images or video streams, is highly useful in the field of autonomous vehicles that rely on discrete object awareness for planning and navigation.
Of the many deep learning-based image segmentation algorithms developed to-date, even the more modern ones exhibit a fundamental tradeoff between accuracy and computational efficiency. 
Thus, few achieve both the required segmentation accuracy and latency/speed for use in real-time settings, as with autonomous navigation.

This project's goal is to investigate the trade off between run-time and accuracy of [FANet](https://github.com/feinanshan/FANet), a state-of-the-art algorithm aimed at real-time applications on video streams, through implementation and experimentation with its hyperparameters. 
We will utilize an existing [automated evaluation pipeline](https://github.com/MSiam/TFSegmentation) that includes a leader board and incorporation with the widely-used CityScapes segmented image dataset. 
We propose investigating the effects of varying temporal information on FANet efficiency (in frames per second) and effectiveness (in mIoU \%). 
The model isn't trained, and therefore it will be trained with temporal span T=2 and will be compared to the authors' result. 
Systematic evaluation will lead to conclusions about the algorithm's suitability for usage onboard an autonomous vehicle.

This work is based off of the following papers:

- [Real-time Semantic Segmentation with Fast Attention](https://arxiv.org/pdf/2007.03815.pdf)
- [RTSeg: Real-time Semantic Segmentation Comparative Study](https://arxiv.org/pdf/1803.02758.pdf)
