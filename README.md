# LibrePlan

A simple, free and open-source day planner and to-do list.

If you often think to yourself, "I wish I had the time to do this," LibrePlan can help you find the time to do it.

Based on [Plan](https://help.supermemo.org/wiki/Plan) and [Tasklist Manager](https://help.supermemo.org/wiki/Tasklist_manager) from [SuperMemo](https://www.supermemo.com), the project originally started as a Excel spreadsheet powered by Visual Basic, but when I decided that I wanted to move to Linux (where Excel is not an option, and LibreOffice couldn't do what I wanted), I decided for portability reasons and ease of maintenance to use Python and PyQt because I thought the UI/UX for [Anki](https://github.com/ankitects/anki/) was well-made.

## Features

LibrePlan helps you to...

- Collect and prioritize a variety of tasks based on your given cost/benefit numbers.
- Fit the most beneficial/desired tasks into your day.
- Make sure that you do them for the amount of time you've promised yourself.
- Better optimize your plans by recording task performance statistics.

## Getting Started With LibrePlan

These two link provide a good introduction on how to use LibrePlan's two main features:

- Plan: [Planning a perfect day with SuperMemo](https://youtu.be/nuftJuUFSbY).
- Tasklist: [Tasklist Manager](https://help.supermemo.org/wiki/Tasklist_manager).

## Building/Installing

The software you will need to build LibrePlan are:

- Python 3.8+, with PIP

On Windows, you will additionally need:

- Git for Windows, for the GNU Coreutils.
- GNU Make, to build the project.
- (Optional) [NSIS](https://nsis.sourceforce.com), to build the installer.

And simply run...

```shell
make
```

... and put the `dist/LibrePlan` directory wherever you want.

On Windows, you can build the installer by running...

```shell
make installer
```

... and then running the installer located in the `dist/` directory.

For testing, just run...

```shell
make test
```

... or by running `pytest` manually.
