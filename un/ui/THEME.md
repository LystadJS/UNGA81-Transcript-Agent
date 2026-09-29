# Email-matched interface

Matches the existing templates/email_head.html and R/04_email.R theme:
navy #062135 masthead, red #D01319 rule, blue #002D74 labels and actions,
white panels, pale #F6F8FA background, #D6DEE7 borders, and the existing USUN seal.
Local outline SVG icons mark setup, review, generation, downloads and result tabs.
Decorative icons are hidden from assistive technology; visible labels remain.

Desktop (1440px) and mobile (390px) static previews verified without horizontal
overflow; seal loads and all ten preview icons render. The actual Shiny UI
constructor renders successfully. No analysis, email generation, or server
controller logic was changed. Full Shiny startup could not be tested here
because the local R installation lacks the zip package. Use ui/Setup.bat to
install the declared dependencies if needed. The HTML preview is read-only.
