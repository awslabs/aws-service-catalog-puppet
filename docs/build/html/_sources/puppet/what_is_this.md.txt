What is this?
=============

This is a framework where you list your AWS accounts with tags and your AWS Service Catalog products with tags or target
accounts. The framework works through your lists, dedupes and spots collisions and then provisions the products into your 
AWS accounts for you. It handles the Portfolio sharing, its acceptance and can provision products cross account and cross 
region.


### High level architecture diagram

![](./whatisthis.png)

You use an AWS CodeBuild project in a central _hub_ account that provisions AWS Service Catalog Products into _spoke_
accounts on your behalf.  The framework takes care of cross account sharing and cross region product replication for you.