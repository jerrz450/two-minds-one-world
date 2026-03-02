from config.settings import settings

_MAX_STEPS = 15
_CAP = 4000


async def browse_web(task: str) -> dict:
    """Launch a browser-use agent to complete a web task.
    Handles JS-heavy pages, multi-step navigation, form filling, etc.
    Returns the agent's final extracted result."""
    try:
        from browser_use import Agent, Browser, BrowserConfig
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0,
        )
        browser = Browser(config=BrowserConfig(headless=True, disable_security=True))
        agent = Agent(task=task, llm=llm, browser=browser)
        history = await agent.run(max_steps=_MAX_STEPS)
        result = history.final_result() or "Task completed but no result was extracted."
        return {"result": str(result)[:_CAP]}

    except ImportError:
        return {"error": "browser-use is not installed in this environment."}

    except Exception as e:
        return {"error": str(e)[:500]}
