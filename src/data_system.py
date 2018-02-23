# This module is meant to simulate the data system of vehicle access node
# We assume for the base model there is no data requests targeted towards specific vehicles 
#
# Each VEH generates data gathered from its surrouding and its passengers. 
# The data generated has a level of urgency for uploading
# Each VEH generates data requests due to its passengers and situation 
# The data requests also has a level of urgency for downloading 
# 
# In terms of data usage, we utilize 3 categories; low, medium, high
# Data based on size
# Status Messages: Small
# Internet Browsing: Medium
# Sensing data: Medium
# Online Games: Medium
# Video streaming: High
#
# In terms of responsiveness, we utilize 3 categories, low, medium, high
# This will depend on what the user needs and is not assigned ahead of time  