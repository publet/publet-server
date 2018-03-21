Custom-hosted publications
==========================

Although Publet can do lots of stuff, occasionally there is need to make custom modifications. To custom host a publicaton from a GitHub repository:

## Publication of status custom

1. Create a GitHub repository and push your code. The repository must be public or have the GH user @`publetbot` have pull access on the repository.
2. Go into Publet.
3. Edit the Publication settings and set `status` to `custom`.
4. Paste your GH clone URL into the `Custom publication origin url:` text field.
5. Save.

## Republishing

1. Make additional code changes and push to GitHub.
2. Go into your Publet publication settings and hit the `Republish` button.
3. Wait 10-15 minutes for server things to happen.
4. Updated code is now shown to your visitors.