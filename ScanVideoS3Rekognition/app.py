#!/usr/bin/env python3

from aws_cdk import core

from scan_video_s3_rekognition.scan_video_s3_rekognition_stack import ScanVideoS3RekognitionStack


app = core.App()
ScanVideoS3RekognitionStack(app, "scan-video-s3-rekognition")

app.synth()
