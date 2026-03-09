# Todolist

- **Category:** Web
- **Solves:** 63

## Description

My friend vibe-coded a todo list website and insists it’s secure because it runs entirely client-side.
Can you take a look and see if that’s actually true?

## Details

The application provides CSTI-as-a-service: you can control both the template and the data it contains. However, because the template engine is Handlebars, you cannot achieve XSS.

Despite this limitation, the JavaScript code includes a Handlebars helper that compares two variables.

```js
Handlebars.registerHelper('eq', (a, b) => a === b);
```

Moreover, the flag is stored by the bot in the template data, and we can use CSRF to force data and templates to be added to the admin account via GET parameters:

?template=<template>&data=<data>

The only thing left is to find a way to leak each character of the flag. One approach is to introduce a sufficiently large delay in template generation. Handlebars supports nested loops, so we can use two or three nested loops to create a measurable delay and detect it with onload.


## Solution

See solve.html for the solve script.