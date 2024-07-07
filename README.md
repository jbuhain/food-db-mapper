# LangualProject
# Updates
  - 7/7/24: added early tests for jaccard_index method, cleaned up repository
# Todo
  - Refactor main.py to have uniform column values
    - Process the raw data to make it easier to use, remove null values etc
## Notes
Not all of the rows have a 1 to 1 specific entry
Not all of the rows have a defined langual code (that's where LLMs becomes handy)

Cross searchable food database consisting databases from Frida and NEVO

Is this project going to be a web app? Or just a local python program. 
For now maybe just stick with a python program and make into a web application later?
Create methods that allows you to search based on the searchable foods from the database 

How do I test the performance of my program? 3 Categories
  - Test 1: 100 fixed food rows. 
  - Test 2: 100 random food rows(done 10 times). 
  - Test 3: [Edge-case testing] pick 30 foods with no langual codes 

Set max rows as a const variable