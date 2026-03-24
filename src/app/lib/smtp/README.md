# Origin
https://medium.com/@abdullahzulfiqar653/sending-emails-with-attachments-using-python-32b908909d73

# Example

```python
mailWrapper = mailer()
mailWrapper.setMailserver(server='openrelay.bit.intern', port=25, tls=False)
mailWrapper.setSender(mailaddress='noreply@bridging-it.de', name='SkillScout Reifegrad Benchmark Tool')
mailWrapper.addTo(mailaddress='michael.oberdorf@bridging-it.de', name='Michael Oberdorf')
mailWrapper.setSubject(subject='This is a testmail')
mailWrapper.setBody(body="This is a testmail\nFrom my python script")
mailWrapper.addAttachment(filename='./README.md')
mailWrapper.send()
```
