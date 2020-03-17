# ReplicationProject

In order to run this please follow the following steps:

1. You must run with target 'rawToLD'.
   This will do two things. First it will download the first 3 zipped files from the Wikipedia Raw Dump data and unzip them. Then it will go through all 3 files and create a light dump file format for each of the Wikipedia pages in the files and write it all to one file called "myOuFile.txt". This file is the light dump data for all the pages in the first 3 zipped files from the website. This contains only page topics starting with "A" and a few starting with "B."
   
2. The next step is to run either target 'testLdToM' or 'LdToM.' The first target will use a light dump .txt file that contains just one article: "Anarchism." It will return the M statistic for that. The second will use the large light dump file: "myOutFile.txt" and give the top 20 and bottom 20 articles based on their m scores.

You much run step one in order to be able to run the target "LdToM". Otherwise you will not have the files listed in the config file.
