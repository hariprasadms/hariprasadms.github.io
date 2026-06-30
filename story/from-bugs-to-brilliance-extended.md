# From Bugs to Brilliance
### A story about software testing in the age of AI
**by Hariprasad Srinivas**

---

## The Full Story Arc (proposed)

Before the new chapter, here is the shape of the whole book — so every chapter pulls toward one destination: Arun's transformation from "testers just click buttons" to the engineer who teaches an entire company how humans and AI test software together.

**Part I — The Awakening (Ch 1–3):** Arun breaks production, meets Meera, learns to think like a tester. APIs, backend defects, the invisible layer.

**Part II — The Craft (Ch 4–6):** Automation. Arun automates everything, then learns the hard way that bad automation is worse than no automation. Flaky tests, locator strategy, what to automate and what to leave human.

**Part III — The Disruption (Ch 7–8):** AI arrives at TechNova. Half the team fears being replaced. Arun makes his biggest mistake yet — trusting AI blindly — and discovers the real skill: directing AI like a junior engineer who never sleeps but never thinks for itself either.

**Part IV — The Teacher (Ch 9–10):** Meera moves on. Arun, now the senior, inherits a new graduate who believes "AI does the testing now." The story comes full circle: the student becomes the mentor, and the final production incident is one only a curious human could have caught.

---
---

# CHAPTER 1 — The Day Everything Changed *(refined)*

---

## Page 1

The rain tapped against the glass walls of TechNova Solutions like a thousand impatient fingers. Arun stood in the reception area gripping a laptop bag that still smelled of the shop, rehearsing his own name in case someone asked for it.

Six years of studying. Eleven rejected applications. Three rounds of interviews. And now a lanyard with his photo on it — slightly blurry, but his. **Software Engineer.** He read the words twice, just to feel them.

Through the glass he watched people stream past: developers arguing over a whiteboard, a manager balancing three coffees, and a quiet corner where a few people sat clicking through screens with strange intensity.

"Who are they?" he asked the receptionist.

"Testing team."

Arun nodded politely. Privately, he felt a small flicker of relief. *Thank God I'm a developer,* he thought. *Imagine spending your whole career clicking buttons.*

He would remember that thought for the rest of his life — the way you remember the last thing you said before a car crash.

## Page 2

The induction session was the usual blur of HR slides — until a senior engineering manager named Priya walked in, picked up a marker, and wrote four words on the whiteboard:

> **QUALITY IS EVERYONE'S RESPONSIBILITY.**

"Memorise it," she said. "It will save your career at least once."

Arun raised his hand — first-day enthusiasm. "Isn't quality the testing team's job? That's why they exist, right?"

A few people chuckled. Priya didn't. She walked closer.

"Last year a bank's mobile app sent payment notifications to the wrong customers. Tell me — do you think any of those customers asked which *team* introduced the bug?" She let the silence work. "Customers never care who broke it. They only know *the product failed them.* The logo on the app takes the blame. And the logo belongs to all of us."

Arun wrote the four words in his new notebook, mostly to look diligent.

Years later, he would write the same four words on a whiteboard himself, in front of a hundred engineers, and tell them this exact story.

## Page 3

Three weeks in, Arun got his first real ticket.

> *TASK-2214: Increase username max length from 30 to 50 characters. Marketing request — corporate clients use long email-based usernames.*

He almost laughed. *This* was the job he'd fought eleven rejections for? He changed one configuration value, updated one line of validation on the frontend, and tested it locally. Logged in with a 45-character username. Worked. Logged in with his own. Worked.

Code review: approved in nine minutes. "LGTM 👍" — Rohan, Senior Developer.

The deploy went out Friday evening. Arun went home, called his parents, and told them the job was going brilliantly. He said, and he would later wish he hadn't, "Honestly, the work is easier than university."

At 2:17 AM on Saturday, while Arun slept, a monitoring system somewhere in a data centre quietly turned red.

By 2:30 AM, it was screaming.

## Page 4

Arun's phone exploded at 7 AM with messages he didn't fully understand:

> *"Login failure rate at 64%"*
> *"SEV-1 declared overnight"*
> *"All hands, war room, Monday 9 AM"*

Monday morning, the war room held more people than Arun's entire graduation row. Dashboards covered the wall — red lines climbing like fever charts. **41,000 failed logins.** Call centre queues overflowing. A banking client demanding a formal incident report.

For an hour, everyone explained why it couldn't be *their* part. Infrastructure blamed deployment. Deployment blamed the release. The release contained exactly one customer-facing change.

Arun's change.

His ears were ringing so loudly he almost missed it when a calm voice from the back row cut through the noise. A senior QA engineer named Meera, asking what sounded like the simplest question in the world:

"What happens when a username exceeds fifty characters?"

Silence.

"The frontend blocks it," Rohan said finally. "There's validation."

"I didn't ask about the frontend," Meera said. "Corporate clients log in through the API. What does the *API* do at fifty-one characters?"

Nobody knew. Eleven minutes later, everybody did: the API had no length check at all. Oversized usernames had been flowing straight into an authentication service that crashed — and restarted — and crashed — taking everyone else's logins down with it.

One missing line. Forty-one thousand people locked out of their bank.

## Page 5

Arun spent the rest of the day waiting to be fired.

Instead, at 4 PM, Meera appeared at his desk holding two coffees. "Walk with me."

They sat in the cafeteria, by the window. Arun couldn't look at her. "I know why this happened," he said. "I wrote bad code."

Meera shook her head slowly. "No. Your code did exactly what you told it to do. That's the tragedy of code — it always does." She slid one coffee across the table. "Here's what actually happened: you tested that your change *worked*. You never tested how it could *fail*. Those are two completely different activities, and only one of them protects customers."

"But it worked on my machine—"

"It always works on your machine," she said, with the weariness of someone who had heard that sentence a thousand times. "Your machine is the politest user your software will ever meet. Real users are chaotic. Real systems fail at 2 AM. Real attackers send fifty-one characters *on purpose.*"

She let him sit with it. Then: "Want to know the question that found your bug in eleven minutes?"

Arun nodded.

"It's a way of thinking. Come find me tomorrow and I'll show you."

## Page 6

The next morning, Meera drew a simple line on the whiteboard by her desk.

"Your username field. Accepts 1 to 50 characters. You're allowed exactly five tests. Where do you spend them?"

Arun thought hard, wanting to redeem himself. "Twenty-five characters. Right in the middle. Then maybe ten and forty?"

Meera laughed — not unkindly. "That's where everyone starts. The middle is the safest place in any system. Nothing interesting has ever happened at twenty-five characters in the history of software." She marked the line at four points. "Defects are border creatures. They live at the edges: **0, 1, 50, 51.**"

```
  0     1      2 ........ 49      50     51
[FAIL][PASS][        ok        ][PASS][FAIL]
  ↑                                      ↑
  the edges — where your bug lived
```

"Zero — what happens with an empty username? One — the minimum boundary. Fifty — the last legal value. Fifty-one —" she tapped the board, "— the exact character that took down forty-one thousand logins on Saturday."

Arun stared at the diagram. His entire outage, the war room, the red dashboards — all of it lived in the single step between 50 and 51.

"Positive testing proves it works," Meera said. "Negative testing proves it fails safely. Boundary testing tells you *where* to look. Three ideas. They'll find more bugs than any tool you'll ever buy."

## Page 7

That afternoon, Arun did something he'd never done in his life: he tried to *break* software on purpose.

The team had just finished a new registration form — developer-tested, peer-reviewed, ready for release. Arun opened it and, instead of filling it in like a polite user, he filled it in like a 2 AM incident waiting to happen.

Email address with no @ symbol? *Accepted.* **Defect one.**

He pasted the entire first chapter of a novel into the "Company name" field. The page froze for eight seconds, then crashed. **Defect two.**

Date of birth: 30th February. The form said *"Welcome!"* **Defect three.**

One hour. Three defects. In a feature that had already "passed" testing.

He sat back, oddly breathless. This didn't feel like clicking buttons. It felt like being a detective in a building where every door might be unlocked. He'd spent three weeks building things and feeling clever. He'd spent one hour breaking things and felt something better: *useful.*

He took the list to the developer who'd built the form, braced for annoyance. Instead the developer stared at the 30th of February bug and said, "...how did I never think of that?"

"Someone taught me to ask how it fails," Arun said. The words felt good in his mouth.

## Page 8

Weeks passed, and curiosity stopped being an exercise and became a reflex.

Arun's notebook — the one from induction, with QUALITY IS EVERYONE'S RESPONSIBILITY on page one — began to fill with questions:

> *What if the network drops mid-payment?*
> *What if two users register the same username at the same second?*
> *What if the user presses the back button right here?*
> *What if the file they upload is empty? Or 2GB? Or not a file at all?*

He started seeing software the way Meera did — not as screens, but as promises. Every field, every button was a promise to a stranger. Testing was simply checking whether the promises held when life got messy.

"You know what makes great testers?" Meera asked him one evening, watching him interrogate a date picker. "It's not tools. It's not even technical skill — that can be learned. It's that they never stopped asking *what if.* Most people grow out of that question by age ten. Testers never do."

Rohan passed by, glanced at Arun's screen, and smirked. "Careful, Arun. Keep hanging around QA and people will start thinking you're one of them."

It was meant as a joke. Maybe even a warning.

Arun noticed, with some surprise, that it didn't sting at all.

## Page 9

One Friday evening, as the office emptied, Meera stopped at his desk and dropped a folder in front of him. An actual paper folder — she was old-school like that.

"Ready for your next challenge?"

Inside was a single printed email. A P1 production defect. A customer charged twice. Words Arun had heard in meetings but never truly understood: *API. Endpoint. JSON payload. Race condition.*

"I don't know what half of this means," he admitted.

"I know," Meera said, already walking away. "That's exactly why it's yours. Everything you've broken so far, you could *see*." She paused at the door, silhouetted against the corridor lights. "Monday, I show you the part of the iceberg under the water. The defects nobody can see — and everybody pays for."

Arun looked at the folder, then at the rain starting against the windows — the same rain as his first day, three months and one lifetime ago.

He smiled and packed the folder into his bag.

## Page 10

**Key Lessons from Chapter 1:**

1. **Quality is everyone's responsibility.** Customers never ask which team broke it — the product takes the blame, and the product belongs to everyone.
2. **Test how software fails, not just that it works.** "It works on my machine" means it survived the politest user it will ever meet.
3. **Defects are border creatures.** The middle of any range is the safest place in software; bugs live at 0, 1, 50 and 51.
4. **Curiosity is a tester's superpower.** Tools can be learned. Never growing out of "what if?" cannot.
5. **Every production incident is tuition.** Arun's 2:17 AM outage cost the company a weekend — and taught him more than six years of study.

**Chapter 2 Preview:** Arun goes below the surface — into APIs, JSON and the invisible layer where a customer was charged £4,820 for nothing, and the only witness is a log file with a timestamp.

---
---

# CHAPTER 2 — The Invisible Layer

---

## Page 1

The folder Meera had dropped on his desk contained a single printed email. Arun read it three times.

> *Subject: URGENT — Customer charged twice, no order created*
> *Priority: P1*
> *Customer impact: £4,820 duplicate payment. Customer is threatening to leave. CEO has been copied.*

Arun frowned. "But I tested the checkout page last week. The button works. The confirmation screen appears. Everything *looks* fine."

Meera pulled a chair beside him. "That's the problem," she said. "You tested everything you can see. This defect lives somewhere you've never looked."

She drew a horizontal line across his notebook, then another below it.

"Above the line is the UI — buttons, forms, screens. Below the line is where the real work happens. APIs, services, databases. Most engineers spend their whole career above the line." She tapped the lower half. "Today, you go below."

## Page 2

Meera opened a tool Arun had never used before: Postman.

"Forget the browser," she said. "The browser is just a polite messenger. When you click 'Pay Now', the browser sends a request to a payment API. The API does the work and sends a response back. We're going to talk to the API directly — no browser, no buttons, no politeness."

She typed a request and hit Send. A wall of text appeared, wrapped in curly braces.

```json
{
  "orderId": "ORD-88291",
  "status": "PAYMENT_TAKEN",
  "amount": 4820.00,
  "orderCreated": false
}
```

Arun stared. "Wait. Payment taken... but order created is *false*? How can both be true at once?"

Meera smiled the way she always did right before a lesson. "Now *that*," she said, "is the right question."

## Page 3

She explained that the checkout was not one action but two: take the payment, then create the order. Two different services. Two different teams.

"And what happens," she asked, "if the first one succeeds and the second one fails?"

Arun thought about it. "The customer pays... for nothing."

"Exactly. The UI showed a friendly error — *'Something went wrong, please try again.'* So the customer tried again. Paid again. Two payments. Zero orders. The screen looked fine both times. The defect was invisible."

Arun felt a strange feeling rise in his chest. Not dread, like the night of the login outage. Something closer to excitement. *Somewhere in this wall of JSON, there's a clue.*

He was starting to enjoy this.

## Page 4

For the next two hours, Arun fired requests at the payment API like a detective interrogating a suspect.

What if the amount is zero? *Rejected — good.*
What if the amount is negative? *Accepted.* He blinked. **Accepted?**

"Meera. MEERA. The API just accepted a payment of minus five hundred pounds."

She walked over, looked at the response, and started laughing. "Congratulations. You've just found a defect where the bank could end up paying the customer. Log it. Severity: critical. And Arun —" she pointed at his screen, "— no browser on Earth would have shown you that. The UI blocks negative numbers. The API doesn't. Attackers don't use the UI."

That sentence lodged itself in Arun's brain permanently:

**The UI is the front door. Attackers come through the windows.**

## Page 5

But the duplicate payment mystery remained. The negative-amount bug was a great find, but it wasn't *the* bug.

Arun reproduced the customer's exact journey in Postman. Payment request — success. Order request — success. He ran it again. Success. Again. Success.

"It works every time," he groaned. "How do I find a bug that won't happen?"

Meera leaned against the desk. "When a defect won't appear, stop asking *what* went wrong. Ask *when*. What was different at the moment it failed?"

Arun pulled up the logs from the night of the incident — a skill he'd avoided learning until the login outage had forced him. He scrolled to the exact timestamp of the customer's payment.

`23:59:58 — payment-service — SUCCESS`
`00:00:01 — order-service — TIMEOUT`

He stared at the timestamps. Then he saw it.

## Page 6

**Midnight.**

The order service restarted every night at midnight for maintenance. A thirty-second window where it was deaf to the world. The customer had clicked "Pay Now" two seconds before midnight. Payment went through at 23:59:58. The order request arrived at 00:00:01 — into the void.

"It's not a code bug at all," Arun said slowly. "It's a *timing* bug. The system has a thirty-second blind spot every single night, and nobody ever tested it because nobody tests at midnight."

Meera nodded. "Race conditions, timeouts, retries — the invisible layer is full of them. Now the real question: how do you *prove* it?"

Arun grinned. He scheduled a test request for 23:59:59 that night, went home, and barely slept.

At 00:00:04 his phone buzzed with the response:

```json
{ "status": "PAYMENT_TAKEN", "orderCreated": false }
```

Caught. Red-handed. In an empty office at midnight, a bug had finally met a tester willing to stay up for it.

## Page 7

The fix itself took the developers twenty minutes — if the order service didn't respond, automatically refund the payment and tell the customer honestly. What took longer was the conversation in the retro meeting.

"Why didn't QA catch this before release?" asked Rohan, a senior developer with eleven years of experience and very little patience.

The old Arun would have stayed silent. The new one didn't.

"Because we only tested *that* checkout works," he said. "Nobody asked *how it could fail*. I've written down eleven failure questions for checkout — what if payment succeeds but the order doesn't, what if the same request arrives twice, what if the service is mid-restart. I'd like to add these to every release going forward."

The room went quiet. Then the engineering manager said the words Arun would remember for years:

"Send that list to everyone. That's not a QA checklist. That's how we should all be thinking."

## Page 8

That evening, Meera found him at his desk, still writing failure questions.

"You know what you did today?" she said. "You didn't just find a bug. You changed how a room full of engineers thinks. That's the part of this job nobody puts on the job description."

She paused at the door. "Oh — and HR emailed me. There's an internal opening on the quality engineering team. Interviews are next month." She let that hang in the air. "You'd have to stop calling yourself a developer."

Arun looked at his notebook — now half-full of failure questions, boundary values, and JSON snippets. Three months ago he had believed testers just clicked buttons.

"What would I even tell my parents?" he half-joked. "They think testing is what people do when they can't code."

Meera laughed. "Tell them you've been promoted from building things to protecting everyone who uses them."

## Page 9

He didn't say yes that night. That's not how real decisions happen.

But on Saturday morning, on his usual walk, Arun caught himself doing something strange. He was looking at a parking meter, thinking: *What happens if I pay exactly when it loses signal? Does it take my money? Where does that transaction go?*

He stood there for a full minute, smiling at a parking meter like an idiot.

That's when he knew. It wasn't a job change. It had already happened — somewhere between a 2 AM login outage and a midnight stakeout in an empty office. The title was just paperwork.

On Monday, he applied.

## Page 10

**Key Lessons from Chapter 2:**

1. The UI is only the surface — most critical defects live in the invisible layer of APIs and services.
2. The UI is the front door; attackers come through the windows. Test the API directly.
3. When a bug won't reproduce, ask *when* it happened, not just *what* happened.
4. Logs and timestamps are a tester's crime scene evidence.
5. A great tester doesn't just find bugs — they change how the whole team thinks about failure.

**Chapter 3 Preview:** Arun joins the quality engineering team and faces his first humiliation — a test suite of 400 manual test cases that takes nine days to run, a release every two weeks, and a manager who asks the question that will define the next phase of his career: *"Why is a human doing any of this?"* The age of automation begins.

---
---

## Notes for Hari (not part of the book)

**What I changed in the storytelling — and why:**

1. **A mystery engine.** Chapter 1 was a sequence of lessons. Chapter 2 is structured as a detective case: a crime (duplicate payment), a false lead (negative amount bug), a clue (timestamps), and a midnight stakeout. Each technical concept (Postman, JSON, race conditions, log analysis) is discovered *because the plot needs it*, not because it's next on a syllabus.

2. **Real stakes.** £4,820, a CEO on the email, a customer threatening to leave. Concrete numbers make the reader feel the cost of a defect.

3. **A rival.** Rohan, the impatient senior dev, gives Arun friction and a moment to show growth. He can recur — and in the AI chapters, Rohan becomes the "AI will replace testers" voice, which is a debate your real audience is living through right now.

4. **An emotional turn per chapter.** Chapter 1: shame → curiosity. Chapter 2: curiosity → identity (the parking meter moment, applying for the QA role). Every chapter should move Arun's *identity*, not just his skills.

5. **Quotable lines.** "The UI is the front door. Attackers come through the windows." Each chapter should produce one line readers will screenshot and share — this is also your LinkedIn marketing content, pre-made.

6. **The AI thread.** I've deliberately held AI back until Part III. The book's argument lands harder if Arun masters human testing *first* — then AI arrives as a disruption he must navigate, mirroring your audience's actual journey. His big AI mistake (trusting it blindly, shipping AI-generated tests that all pass because they test nothing) becomes the modern version of his Chapter 1 outage.

**Next steps — tell me which you want:**
- Write Chapter 3 (automation begins, the 400-test-case problem)
- Jump ahead and draft Chapter 7 (AI arrives) to lock the book's biggest moment early
- Adjust anything about Chapter 2's tone, length, or technical depth first
