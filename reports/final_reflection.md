# Sprint 4 — Final reflection

One short reflection per teammate: what you found **most rewarding** about completing the Sprint 4 project (and the course project overall, if you like).

---

## Salem Al Shamsi

**Contributions**

Trainer create-class plus wiring the classes part of the app; fixes for tokens, capacity, signup fields, and date/JSON issues.

Automated tests for trainer roster and email-reminder flows; resetting the mocked database between test runs.

Updates to requirements and the use-case diagram; Sprint 3 design reflection with screenshots; notes on the refactor in `redesign.md`.

Merging teammates’ work into `main`.

Overall I learned how to work in a group, how to make our code efficient and understandable. Maintaining code and keeping it clean was a bit hard, but that was one of the most important things I learned from the class. Learning about containers and how they work was nice and will help me in my future projects. Thanks.

---

## Sami Akouk

My contributions spanned the full lifecycle of the project — from initial setup to production deployment. In Sprint 1, I laid the
foundation by designing the database schema and building the authentication layer, which every other feature in the project depends
on. In Sprint 2, I took ownership of the CI pipeline, which became a safety net that the whole team relied on for the rest of the
project, ensuring no broken code made it into main. In Sprint 3, I contributed to the design reflection and then implemented Feature 6, the recurring classes extension. This required understanding the existing class creation flow deeply and extending it without breaking existing functionality. In Sprint 4, I was responsible for containerization and continuous deployment. Writing the Dockerfile and docker-compose.yml meant the app could run consistently on any machine without manual setup. The CD workflow closed the loop by automating deployment to the EC2 VM whenever CI passes.

I knew most of the technologies, practices, and technologies used from previous experiences, but it was still fun to apply it again.

---

## Zayed Al Tamimi

Throughout this project, I gained a deep understanding of the importance of properly designing a system before implementation, specifically through the use of Class and Sequence diagrams. The most challenging aspect was managing the class diagram complexity during Sprint 3B because we applied significant class extraction, which resulted in a system with more classes and connections. I found the most rewarding part of this process to be the development of the Bonus Frontend GUI; after designing the backend, seeing the actual user interface come together felt like bringing the entire project "full circle". My most valuable takeaway, however, was learning optimization techniques regarding code smells, which taught me how to improve maintainability and remove redundancy. These are skills I can now apply to any project beyond software development. Ultimately, I am now more aware of how to plan a system effectively and have successfully delivered a complete piece of software with a great team!

---

## Ibrohim Iskandarov

Most rewarding part was learning to work in a team. Firstly, to allocate tasks fairly and taking into account the availability of other teammates. Making sure that for bottleneck tasks we choose teammates who are available in the beginning of the sprint for example. Loved it, taught me a lot. Another thing I found really rewarding was the ease of building UI given how our code was well-organized and followed the design and coding principles. I built a demo which ended up not being implemented in the project. 