import genanki
import random

ANKI_MODEL_ID = random.randrange(1 << 30, 1 << 31)

ANKI_MODEL = genanki.Model(
    ANKI_MODEL_ID,
    'AutoQuiz Multiple Choice (Recall)',
    fields=[
        {'name': 'Question'},
        {'name': 'Choices'},
        {'name': 'CorrectAnswer'},
        {'name': 'Explanation'},
        {'name': 'AppStats'},
        {'name': 'Source'},
    ],
    templates=[
        {
            'name': 'Recall Card',
            'qfmt': '''
<div style="font-size:18px; font-weight:600;">
{{Question}}
</div>

<hr>

<div style="font-size:16px; margin-top:10px;">
{{Choices}}
</div>
''',
            'afmt': '''
<div style="font-size:18px; font-weight:600;">
{{Question}}
</div>

<hr>

<div style="font-size:16px; margin-top:10px;">
{{Choices}}
</div>

<hr>

<div style="font-size:16px; color:#2ecc71; font-weight:bold;">
Correct Answer:
</div>

<div style="font-size:16px; margin-top:6px;">
{{CorrectAnswer}}
</div>

{{#Explanation}}
<hr>
<div style="font-size:14px;">
<b>Explanation:</b><br>
{{Explanation}}
</div>
{{/Explanation}}

{{#AppStats}}
<hr>
<div style="font-size:13px; color:#888;">
<b>Stats:</b><br>
{{AppStats}}
</div>
{{/AppStats}}

{{#Source}}
<hr>
<div style="font-size:12px; color:#aaa;">
Source: {{Source}}
</div>
{{/Source}}
''',
        },
    ],
)
