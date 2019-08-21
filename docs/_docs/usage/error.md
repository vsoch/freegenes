---
title: Error Pages
description: FreeGenes has custom error pages
---

# Error Pages

When running in non-debug mode, meaning that DEBUG is set to False in your
settings:

```python
DEBUG=False
```

If the user hits a 404 (page not found) we show them a custom view:

![404.png]({{ site.baseurl }}/docs/usage/404.png)

If the user triggers a server error, we show them a different view:

![500.png]({{ site.baseurl }}/docs/usage/500.png)

There is currently no backend error logging configured, but this can be easily 
setup to alert us when the user triggers an error (for example, [Sentry](https://sentry.io) is
a good service).
