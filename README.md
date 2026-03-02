# Avaya-CDR-listener
alternative to _list bcms skill_ but for regular hunt groups 


**Description:**
 - script listens on port 5144 UDP (configurable) 
 - matches only extensions 75xx & 10xx (configurable)
 - if the call is answered by station in monitored range, call is appended to csv as Answered 
 - if call is not answered by station in monitored range and redirected back to huntgroup, call is appended to csv as RONA
 - based on Av-Global-Session-id, a new enty with redirected call is appended to csv as Answered (both rona call and redirected call will have same Av-Global-Session-id)
 - rejected calls will count as rona, if you have correct configuration of coverage path
   
**Disadvantages:**
if vdn is in same range as monitored stations (ie station range 10xx and vdn= 1000) script will not work properly.
Best if you have vdn outside range or different lenght.

**Advantages:**
- you can use mutt to email csv daily
- you can make an alternate script to count answered/unanswered calls for each user/vdn daily/montly on antoher csv or insert into a postgresql table
  
**Output:**
in /var/logs/avaya_cdr (configurable) there will be an csv per day sip_events_yyyy-mm-dd.csv that will have: date, time, calling number, vdn, station, call state, Av-Global-Session-id

<img width="739" height="96" alt="image" src="https://github.com/user-attachments/assets/802e0fde-1364-49d7-902e-5a954165f700" />

