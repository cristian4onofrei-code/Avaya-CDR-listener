# Avaya-CDR-listener
alternative to _list bcms skill_ but for regular hunt groups 

**Requirements:**
- Onex Communicator SIP registered to Session Manager
- all Session Managers configured with remote Syslog server
- systemd service on syslog server that runs python script
- ddi routed to a vdn with _cov y if unconditionally_  (required for rona only)
- Hunt Group has coverage path to itself (required for rona only)
- depending on call volume, you need a cronjob to cleanup cdr outputs
  
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

2026-03-02,21:09:03,+40756147424,654325,1003,ANSWERED,426a98f0-166b-11f1-a9a1-0050568cb03a
2026-03-02,21:12:48,+40756147424,654325,1002,RONA    ,c9f3b5e0-166b-11f1-a9a1-0050568cb03a
2026-03-02,21:12:50,+40756147424,654325,1003,ANSWERED,c9f3b5e0-166b-11f1-a9a1-0050568cb03a
2026-03-02,21:31:15,+40756147424,654325,1002,RONA    ,5df1b010-166e-11f1-a9a1-0050568cb03a
2026-03-02,21:31:18,+40756147424,654325,1003,ANSWERED,5df1b010-166e-11f1-a9a1-0050568cb03a
