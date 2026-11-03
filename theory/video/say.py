"""Spoken-only respellings for the whole course: the caption keeps the real word. Longest keys first."""
_S = {
 "gcloud":"gee-cloud","gsutil":"gee-s-util","kubectl":"kube-control","bq":"B-Q","cbt":"C-B-T",
 "IAM":"I-A-M","VPC":"V-P-C","VPCs":"V-P-Cs","GKE":"G-K-E","GPU":"G-P-U","GPUs":"G-P-Us","TPU":"T-P-U","TPUs":"T-P-Us",
 "CMEK":"see-mek","CSEK":"see-sek","NGFW":"N-G-F-W","OIDC":"O-I-D-C","SAML":"sam-ul","SCIM":"skim","GCDS":"G-C-D-S","IdP":"I-D-P","IdPs":"I-D-Ps",
 "KMS":"K-M-S","ADC":"A-D-C","CUD":"C-U-D","CUDs":"C-U-Ds","SSD":"S-S-D","IAP":"I-A-P","SSH":"S-S-H","BGP":"B-G-P","DNS":"D-N-S",
 "API":"A-P-I","APIs":"A-P-Is","CLI":"C-L-I","SDK":"S-D-K","IaC":"I-A-C","MIG":"mig","MIGs":"migs","HA":"H-A","VM":"V-M","VMs":"V-Ms",
 "SLO":"S-L-O","SLOs":"S-L-Os","SLI":"S-L-I","SLIs":"S-L-Is","SLA":"S-L-A","CDN":"C-D-N","TLS":"T-L-S","SSL":"S-S-L","HTTPS":"H-T-T-P-S","HTTP":"H-T-T-P","TCP":"T-C-P","UDP":"U-D-P","ICMP":"I-C-M-P","RDP":"R-D-P","IP":"I-P","IPs":"I-Ps","CIDR":"cider","MTU":"M-T-U","NAT":"nat",
 "RPO":"R-P-O","RTO":"R-T-O","TTL":"T-T-L","SQL":"sequel","NoSQL":"no-sequel","MySQL":"my-sequel","PostgreSQL":"Postgres","CEL":"C-E-L","JWKS":"J-W-K-S","JWT":"J-W-T","STS":"S-T-S","ACL":"A-C-L","ACLs":"A-C-Ls","RBAC":"are-back","HPA":"H-P-A","VPA":"V-P-A","PD":"P-D","NFS":"N-F-S","HDD":"H-D-D","GCS":"G-C-S","OSS":"O-S-S","PITR":"P-I-T-R",
 "Pub/Sub":"pub sub","ID":"I-D","IDs":"I-Ds","AD":"A-D","LDAP":"el-dap","YAML":"yamel","HCL":"H-C-L","DLQ":"D-L-Q","AWS":"A-W-S","PAM":"pam","FinOps":"fin-ops","vCPU":"V-C-P-U","vCPUs":"V-C-P-Us","IOPS":"eye-ops","HMAC":"H-mac","S3":"S-three","ACE":"ace","MCP":"M-C-P","ETL":"E-T-L","EU":"E-U","CI":"C-I","CI/CD":"C-I-C-D","QPS":"Q-P-S","AZ":"A-Z","GA":"G-A","OLTP":"O-L-T-P","OLAP":"O-lap","URL":"U-R-L","URLs":"U-R-Ls","RAM":"ram","VM's":"V-M's",
 "etag":"E-tag","DDoS":"D-doss","VMware":"V-M-ware","vSphere":"vee-sphere","X.509":"X-five-oh-nine","IPv4":"I-P-v-four","IPsec":"I-P-sec","rsync":"R-sync","cp":"C-P","RBAC":"are-back","Autopilot":"Auto-pilot","Hyperdisk":"Hyper-disk","Bigtable":"Big-table","Memorystore":"Memory-store","Filestore":"File-store","Dataflow":"Data-flow","Dataproc":"Data-proc","Cloud NAT":"cloud nat","Kubernetes":"Koo-ber-net-ees",
}
SAY = dict(sorted(_S.items(), key=lambda kv: -len(kv[0])))
