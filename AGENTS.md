# Rule: Prevent Duplicate Work
trigger: always_on

Before building any new component, utility, or feature, you must always thoroughly search the existing codebase to check if an implementation or something similar already exists. Do not duplicate existing functionality.

# Rule: Prevent Platform Account Flagging (Anti-Spam Protocol)
trigger: always_on

When designing, testing, or executing automated outreach campaigns (such as cold WhatsApp messaging, email, or direct messaging):
1. **Never use high-frequency messaging on personal accounts.** Always enforce strict rate-limiting. For personal WhatsApp accounts, limit new chat initiations to a maximum of 5 per day, with random delays of at least 15 to 30 minutes between chats.
2. **Prevent Message Fingerprinting.** Avoid sending identical or minimally modified templates. Always implement high-entropy text variation (e.g. customized opening sentences, distinct structural formatting, and dynamic vocabulary swapping).
3. **Prioritize Official APIs.** For bulk or scaled campaigns (>5 messages/day), default to proposing official API architectures (like Meta's WhatsApp Cloud API) instead of browser automation.
4. **Use Advanced Stealth Mode.** Any browser-based automation (Puppeteer) must use stealth configurations, real non-headless user-agent profiles, dynamic viewport handling, and randomized realistic mouse/typing interactions.
5. **Fail-safe Halt.** If any platform warning or restriction occurs, halt all automation processes immediately and alert the user.

