I would like to make some big changes to the application. 
The goal is to create a radio station of streaming music based on a users preferences.


I would like your input on how I can change the home screen to handle the news capabilities and the radio stations. 
Would a menu make sense that allows to select the news or radio ?
Based on that we can use the current home page for news and create a new page for the radio stations. 
the radio station page should be able to display all radio stations and have (+) button or icon that loads a new page 

The page should have the following components
* Text " create your own radio station based on what music you like or what mood you are in"
* First field should be the name of the 
* an button to allow for loading an image , once selected, display it. 
* a text input field with the title " describe the music you would like to hear " . this is a free form field ( name it "description") where user can enter text like " I love classic rock from the 90s" 
* Next to the input field put a litte (i) infor icon where the following text is shown when the mouse moves over it:  describe the genre and also priode of music. also a mood is very helpful
* another text field with the title : please provide 3 - 5 song examples. This field should be called "example" 
* last field should be duration  of play list. provide a drop down with 1-24 hours. this field should be called "duration"

the page should have a cancel and save button
when cancel is clicked, return to the home screen. 
when save is clicked, please save the new radio station in the database. If the user didn't assign a picture, auto assign a default image/ icon ( something like a guitar).
 to store the radio station  create a new table called stations and use it store the captured data ( including image) linked to the current user ( using the proper id field).
 Once saved, refresh the home screen and display all stations with name, image and highlight of the station description.
when creating the UI, stay with the existing theme and look and feel.
please create new functionality in the existing api for the UI to use.  
Please propose an implementation plan and let me approve before coding. 