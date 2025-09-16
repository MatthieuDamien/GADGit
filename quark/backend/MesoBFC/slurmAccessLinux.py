import pexpect

mot_de_passe = "mdp"
child = pexpect.run("ssh -X umw040ir@login-1.mesobfc.fr")
child.expect("Password:")
child.sendline(mot_de_passe)
child.interact()  # Passe le contrôle au terminal
