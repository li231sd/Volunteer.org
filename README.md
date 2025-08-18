# Volunteer.org
#### Video Demo:  https://youtu.be/yiV0YpSmPW0
#### Description:
Volunteer.org is a comprehensive site made with Python/Flask, and it is where people can list opportunities safely, and people can find opportunities in an organized and managed space. This is the central hub for all volunteers to go to find opportunities and build their profile! A major focus was security, and throughout the entire process, fail-safes were added to prevent any misconduct. 

The site has features such as being able to register an account with checks built in to make sure all information is correct. There is also a login tab to allow users to log into their accounts. If information is entered incorrectly, they will be redirected back to the login with a message above the form, where it will show the exact reason for this redirect. The same is true for register. One cool check is the email check, which can check the style of email given from the server-side.

From here, users are redirected to the Home page, where they will see a list of opportunities they can learn more about. This entire site is mobile-friendly and will adjust thanks to Bootstrap grids! 

There will be a button under every card that redirects them to a template dynamically filled with information regarding that specific opportunity. This happens by getting the ID through the POST request from the card and retrieving info from the database, and putting it into the site. It will show them information about the organization, what the activity consists of, and what dates it will occur. From there, users have an option at the bottom of the page to go back or register for the opportunity with a confirmation message before the POST request goes through. This allows us to make sure the user does not accidentally press the button! These post requests are not made in the traditional form, but rather a fetch request! 

If you notice on the home page that some card descriptions have ... because they are restricted for the amount shown to allow for a cleaner look.

All events users sign up for will be visible in the history tab of the website, where there will be two tables consisting of activities they are running and have joined. The "joined" table will show info such as Event ID, Organization Name, Start Date/Time, and End Date/Time. The "hosted" table will show Application ID, Approval ID, Application Name, Date Approved, Start Date/Time, and End Date/Time.

All users can start their events using the Register Event tab. Here, users will provide tons of information about themselves and their activity. This information is crucial as it will be examined by a Staff member on the next step. After they enter their information and agree to the terms, they will submit their application for review.

Once an application has been submitted, a staff member can log in through the staff portal, where they will see pending applications. Staff accounts are different than regular users, and if a staff member is signed on to the session, all users will be logged out of the current session. Here, they will get information about the account that sent it and the information the user typed in. Staff have two options: they can either approve the application or deny the application. Both an approval and a denial show up in the staff history.

Staff sites also operate through a different template, and staff accounts cannot log into the regular site!

Once an option is selected, as mentioned earlier, it will be added to the history as a record. Also, if the application was approved, it will now show up on the home screen as another card. Checks are implemented to ensure no dual enrollment in the same opportunity, and an organizer cannot register for his/her event.

All database aspects of this site are through the SQLite database!

Thank you for taking the time to read through my CS50x Final Project! I spent around a week designing it!

If you would like to try the staff site the username = admin and password = admin-password.
