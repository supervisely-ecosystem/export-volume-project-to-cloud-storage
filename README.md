<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/48913536/214856590-087865b1-c535-4f12-a593-06e886becdc4.png"/>

# Export volume project to cloud storage

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a> •
  <a href="#Example">Example</a>
</p>


[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](../../../../supervisely-ecosystem/export-volume-project-to-cloud-storage)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/export-volume-project-to-cloud-storage)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/export-volume-project-to-cloud-storage.png)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/export-volume-project-to-cloud-storage.png)](https://supervisely.com)

</div>

# Overview

This app allows exporting volume projects with annotations (in [Supervisely format](https://developer.supervisely.com/api-references/supervisely-annotation-json-format)) to the most popular cloud storage providers from Supervisely Private instance.

List of providers:
- Amazon s3
- Google Cloud Storage (CS)
- Microsoft Azure
- and others with s3 compatible interfaces

✅ For developers: you can use the sources of this app as a starting point for your custom export to the cloud. 

# How To Run

## Run from Ecosystem

1. Run app from the ecosystem

<div align="center" markdown>
  <img src="https://user-images.githubusercontent.com/48913536/214864650-4baae642-ef8f-4e38-9212-510c2613fd7e.png"/>
</div>

2. Select the project, and provider, enter the bucket name, and press the **Run** button in the modal window

<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/48913536/214860601-28cb2962-6801-4331-8c62-16eee2f85f02.png" width="650"/>
</div>

## Run from Volumes Project

**Step 1.** Run the application from the context menu of the Volumes Project

<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/48913536/214860503-084fafe2-cf23-48af-8cce-79735c887bce.png">  
</div>

**Step 2.** Select the provider, enter the bucket name, and press the **Run** button in the modal window

<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/48913536/214860535-72f7f867-295d-4c59-ac1d-9e6453a2ec17.png" width="650">
</div>

# How To Use

0. Ask your instance administrator to add cloud credentials to instance settings. It can be done both in .env 
   configuration files or in the Admin UI dashboard. Learn more in docs: [link1](https://docs.supervisely.com/enterprise-edition/installation/post-installation#configure-your-instance), 
   [link2](https://docs.supervisely.com/enterprise-edition/advanced-tuning/s3#links-plugin-cloud-providers-support). 
   In case of any questions or issues, please contact tech support.
2. Run the app from the context menu of the project you would like to export
3. In the modal window choose desired cloud provider and define the bucket name (the bucket has to be already created)
4. Press RUN button
5. The project will be exported to the following path: `/<bucket name>/<project name>`

# Example

Before the import bucket is empty:

<img src="https://user-images.githubusercontent.com/48913536/214879028-dcc66020-a972-4a56-b40d-01117b325d64.png"/>

After import the project data (volumes and annotations) is in the bucket:

<img src="https://user-images.githubusercontent.com/48913536/214883246-f0dececb-64ea-4aec-a048-394445960293.png"/>
