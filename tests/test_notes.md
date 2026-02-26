# Test 1
> A little unorganised, but the aim for Test 1 is to run through the entire web app. Starting on every single homepage feature, then moving onto the other pages (focus) and then wrapping it up with login / logout.
>   - In Test 2 I'll have to provide special cases + test data (e.g what happens if an integer is too high? And maybe simulate all kinds of users)


**Test 1 outline**:
1. Test 1 [A - F]: Add button on homepage
2. Test 1 [G - I]: Remove button on homepage
3. Test 1 -: Focus page (dropdown, start, pause, stop, db updated)
4. Test 1 -: Insights page (though testing this is useless through my current means, it'll be of use when I create user dummies)
5. Test 1 -: Login + Logout + Register

__Test 1A: Adding Subject__
Subject name: `SUBJECT NAME`
Subject added to DB: Yes
Evidence: ![Adding subject frontend error](test_screenshots/test1_a/netError1.png)
Notes:
> For some reason, it displayed "error - check if server is running". The backend logic works, but it seems to not be in sync with the frontend somehow.
> Sidebar updates automatically (no need to reload) - good
**{-}**

__Test 1B: Adding a subject with a matching name as an already existing subject__
Subject name: `My Subject` (it already exists, both on sidebar and on DB)
Notes:
> When I add it via the web: Currently I didn't fix the issue from Test 1A. But that front end issue aside, on the terminal it seems to be adding a duplicate or some sort? I'll have to query the database to see properly
> No duplicates appear on the sidebar even after reloading - which is a good sign. The sidebar doesn't distinguish subjects by name, rather by id, so duplicates in theory would appear on the sidebar
Evidence: ![Duplicate subjects: API sending it which is fine](test_screenshots/test1_a/dupe_subject.png)

__Test 1C: Adding Module__
Module name: `Module` (under `Subject NAME`)
Module added to DB: Yes
Evidence (if any): ![Module added seamlessly](test_screenshots/test1_a/add_module.png)
Notes: 
> Worked as expected. No issues.

__Test 1D: Adding a Module with the same name as another module under the same Subject__
Module name: `Module` (under `Subject NAME`) (EXISTS already, as per test 1C)
Module added to DB: Doesn't seem like it
Notes:
> Evidence same as 1C. However, just like 1B, nothing appears on the sidebar which may be a good sign. I'll test this on test 2.

__Test 1E: Adding a Sub Module__
Sub Module name: `Sub Module` which is under `Module` (under Subject `Subject NAME`)
Sub Module added to DB: YES (no page reload required)
Evidence (if any): ![Sub Module added seamlessly](test_screenshots/test1_a/add_subModule.png)
Notes:
> Worked as expected, no issues.

__Test 1F: Duplicate Sub Module under the same ancestry__
Sub Module name: `Sub Module` which is under `Module` (under Subject `Subject NAME`) => Already exists as per 1E
Sub Module added to DB: Appears in terminal again, but doesn't seem like it (nothing on sidebar after reloading)
Evidence: same as 1E just repeated
Notes:
> Again, will have to be tested on test 2

__Test 1G: Removing Subjects__
Subject to be removed: `Subject NAME`. It has children (modules, submodules).
Subject removed: Yes (+ sidebar automatically updated)
Evidence: ![Subject removed seamlessly](test_screenshots/test1_a/remove_subject.png)

__Test 1H: Removing Modules__
*I'll create a new subject, `Subject` and then a new Module under it, `Module`, and delete the Module*
Module to be removed: `Subject`.`Module`
Module removed from DB: YES
Evidence: ![Module removed seamlessly - it's also removed from sidebar](test_screenshots/test1_a/remove_module1.png)
Notes:
> Whilst you don't need to reload for the sidebar to update, there are other places where you need to reload for. In the remove/add boxes (modals) they aren't updated unless the page is reloaded. This is one example, there could be examples in the future. I think from here on out I need to find a way to automatically update everything centrally OR force reload again until further notice.

__TEST 1I: Removing Sub Modules__
*I'll create a new subject, `Subject` and then a new Module under it, `Module` and a Sub Module underneath it, `Sub Module`*
Module to be removed: `Subject`.`Module`.`Sub Module`
Sub Module removed from DB: YES
Evidence: ![Sub Module removed seamlessly - it's also removed from sidebar](test_screenshots/test1_a/remove_SubModule.png)
Notes:
> No new issues that haven't been addressed already (1h). That aside, it works fine.

__TEST 1J: Focus page dropdown (does it display all s/m/sm?)__
- Yes
- Evidence:
    - ![Focus dropwdown](test_screenshots/test1_a/focus_dropdown.png)
- Notes:
    - > Functionality works as expected but the UX / design sucks - it's hard to tell + some text don't appear on the whole dropdown on a 1920x1080p screen.

__TEST 1K: Focus page: Start timer__




Future additions/fixes:
- Red warning text on add modal keeps appearing "randomly". This should easily be fixable.
- When adding a s/m/sm, allow the user to hit the `enter` key as well for faster addition.