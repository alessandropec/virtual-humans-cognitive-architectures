# OpenWeather API key: five-minute setup

## 1. Create your account

Open [OpenWeather sign-up](https://home.openweathermap.org/users/sign_up), register and confirm your email. Check Spam if the verification message does not arrive.

## 2. Copy your personal key

Sign in and open [API keys](https://home.openweathermap.org/api_keys). Copy the key shown in your account. You can also generate an additional key there and give it a recognizable name, such as `virtual-human-course`. The key is called **API key** or **APPID**.

A ChatGPT, Codex or Ollama key does not authenticate OpenWeather.

## 3. Check access and activation

For this exercise use **Current Weather** and **Geocoding**, included in the [Free Weather API access](https://openweathermap.org/price) section. The exercise does not use the separate One Call product. Check the current account limits before class.

OpenWeather says activation is automatic and can take **up to two hours after registration**. Create the account before the lesson. [Official FAQ](https://openweathermap.org/faq)

## 4. Configure the agent

Open the existing local file:

```text
virtual_human_project/vh_cognitive_architecture_server/llm_provider_api_key.yaml
```

Keep your existing provider entries and add:

```yaml
openweather:
  api_key: "PASTE_YOUR_OPENWEATHER_KEY_HERE"
```

Replace the placeholder with your actual key, retaining the quotes and indentation. The instructor's local meteorologist already reads this entry. In your exercise, make your weather tool read `openweather.api_key` from this same YAML file.

Alternatively, the tool can read `OPENWEATHER_API_KEY` from the process environment. Start or restart the cognitive server from an environment that contains it. If both are configured, the instructor solution uses the environment value first.

Save the file and restart the cognitive server. Keep the real key in this local configuration, which is excluded from Git; do not paste it into slides, notebooks or the Codex prompt.

## 5. Try a weather question

With your completed weather agent selected, ask: **What is the weather in Rome, Italy?** The avatar should report the observation and display its condition icon.

| Result | What to check |
| --- | --- |
| Key not configured | Replace the placeholder in the correct server YAML, or configure the environment, then restart. |
| HTTP 401 | Check the copied key, activation time and access to the requested product. |
| HTTP 429 | Check account limits and wait before retrying. |
| Weather works but no image | Check that the embodiment server is running and the image upload succeeds. |

Official sources: [Getting started](https://openweathermap.org/appid), [API keys](https://home.openweathermap.org/api_keys), [FAQ](https://openweathermap.org/faq), [pricing and included APIs](https://openweathermap.org/price).
