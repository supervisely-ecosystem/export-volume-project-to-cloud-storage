<div align="center" markdown>
<!-- <img src="https://user-images.githubusercontent.com/106374579/183424972-011d8a6e-1f07-4c34-8ca1-4eff27d71438.png"/> -->

# Export volume project to cloud storage

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a> •
  <a href="#Example">Example</a>
</p>


[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/export-volume-project-to-cloud-storage)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/export-volume-project-to-cloud-storage)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/export-volume-project-to-cloud-storage.png)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/export-volume-project-to-cloud-storage.png)](https://supervise.ly)

</div>

# Overview

This apps allows to export volume project with annotations (in [Supervisely format](https://developer.supervise.ly/api-references/supervisely-annotation-json-format)) to the most popular cloud storage providers from Supervisely Private instance.

List of providers:
- Amazon s3
- Google Cloud Storage (CS)
- Microsoft Azure
- and others with s3 compatible interfaces

✅ For developers: you can use the sources of this app as a starting point for your custom export to cloud. 

# How To Run

## Run from Ecosystem

1. Run app from the ecosystem

<div align="center" markdown>
<!-- <img src="https://user-images.githubusercontent.com/48913536/180185094-853935da-ae2e-4416-97a6-fbe164f9c3c4.png"/> -->
</div>

2. Select project, provider, enter the bucket name and press the **Run** button in the modal window

<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/79905215/214830070-c1356865-523d-4720-8f2e-211c9b7d2339.png" width="650"/>
</div>

## Run from Volumes Project

**Step 1.** Run the application from the context menu of the Volumes Project

<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/79905215/214827452-3a4b54b6-e123-47a9-ac5f-a29c63ad4720.png">  
</div>

**Step 2.** Select provider, enter the bucket name and press the **Run** button in the modal window

<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/79905215/214830090-83244745-4833-4451-9c0e-02003e766c2a.png" width="650">
</div>

# How To Use

0. Ask your instance administrator to add cloud credentials to instance settings. It can be done both in .env 
   configuration files or in Admin UI dashboard. Learn more in docs: [link1](https://docs.supervise.ly/enterprise-edition/installation/post-installation#configure-your-instance), 
   [link2](https://docs.supervise.ly/enterprise-edition/advanced-tuning/s3#links-plugin-cloud-providers-support). 
   In case of any questions or issues, please contact tech support.
2. Run app from the context menu of project you would like to export
3. In modal window choose desired cloud provider and define the bucket name (bucket has to be already created)
4. Press RUN button
5. The project will be exported to the following path: `/<bucker name>/<project name>`

# Example

Before import bucket is empty:

<img src="https://user-images.githubusercontent.com/12828725/180176958-4b14654b-ba9a-4882-b0e6-3dbfee224035.png"/>

After import the project data (volumes and annotations) is in bucket:

<!-- https://user-images.githubusercontent.com/12828725/180199053-5571ecf1-e26c-479e-836d-1d5ef0084873.mp4 -->