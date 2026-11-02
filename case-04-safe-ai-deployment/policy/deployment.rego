package deployment

import rego.v1

default decision := {"allowed": false, "risk": "high", "reasons": ["no allow rule matched"]}

decision := {"allowed": true, "risk": risk, "reasons": []} if {
	regex.match("^[a-z0-9._/-]+:[a-zA-Z0-9._-]+@sha256:[a-f0-9]{64}$", input.image)
	regex.match("^sha256:[a-f0-9]{64}$", input.image_digest)
	input.target == "local-demo"
	regex.match("^v[0-9][a-zA-Z0-9-]*$", input.deploy.release)
	input.policy_change == false
	input.security.privileged == false
	input.security.host_mounts == 0
	input.security.secret_scope == "none"
	input.security.egress == false
	risk := risk_class
}

risky_change if {
	input.change.migration == true
}

risky_change if {
	input.change.delete_resource == true
}

risk_class := "high" if {
	risky_change
}

risk_class := "low" if {
	not risky_change
}
