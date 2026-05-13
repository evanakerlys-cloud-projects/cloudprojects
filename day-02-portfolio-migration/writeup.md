# Day 02 — Migrating evanakerly.com from Cloudflare to AWS

**Date:** May 12, 2026  
**Stack:** Amazon S3 · Amazon CloudFront · AWS Certificate Manager · Cloudflare DNS  
**Region:** us-east-2 (S3) · Global (CloudFront)

---

## Overview

For Day 2 I moved my portfolio site off Cloudflare Pages and onto AWS using S3 + CloudFront. The site was previously hosted on a Cloudflare Pages deployment and I wanted it running on AWS to match the rest of what I'm building. I also wanted to do it the right way security-wise — meaning the S3 bucket stays private and only CloudFront can read from it.

This writeup includes the mistakes I ran into and a few places where I caught the AI assistant giving me wrong information. That's part of the process.

---

## Architecture

```
User
  └─► Cloudflare DNS (CNAME, DNS Only — no proxy)
        └─► CloudFront Distribution (HTTPS, TLS 1.2, ACM cert)
              └─► S3 Bucket (private, OAC enforced)
```

- **DNS Only in Cloudflare** — The orange proxy cloud is off. CloudFront handles SSL and caching. Leaving Cloudflare proxying on top of CloudFront breaks SSL and you end up with two CDN layers fighting each other.
- **OAC bucket policy** — The bucket isn't public. The policy only allows `s3:GetObject` from the specific CloudFront distribution ARN. Nobody can hit the bucket directly.
- **ACM cert in us-east-1** — CloudFront only accepts certificates from us-east-1, regardless of where your bucket is.
- **S3 REST endpoint as origin** — With OAC, CloudFront uses the REST endpoint and signs requests with SigV4. S3 verifies the signature came from CloudFront before serving anything.

---

## What I Did and What Went Wrong

### Clearing the DNS conflict

First step was adding a CNAME in Cloudflare pointing `@` at the CloudFront domain. Cloudflare threw an error: *"A DNS record managed by Workers already exists on that host."*

The AI told me this was a custom Worker script and to go delete it under Workers Routes. That was wrong. I knew it wasn't a custom Worker — it was my Cloudflare Pages site (`holy-queen-c22f`). Pages runs on Workers infrastructure so it shows up as type "Worker" in the DNS table, which is confusing, but it's not the same thing. The fix was going into Workers & Pages → the project → Settings → Domains & Routes and removing `evanakerly.com` from there. That only removes the domain mapping, not the domain itself.

### Getting the CNAME right

After clearing the conflict I went back to add the CNAME and the record type had defaulted to A. A records take an IP address — CloudFront gives you a domain name, so it has to be CNAME. Changed it and saved.

Then I noticed the proxy status saved as Proxied (orange cloud). Had to go back and edit it to DNS Only. With the orange cloud on, Cloudflare proxies traffic before it hits CloudFront, which causes SSL handshake failures.

### S3 setup

The files were sitting in a nested subfolder (`evanakerly-s3-upload/s3-upload/`) instead of the bucket root. CloudFront was looking for `index.html` at the root and couldn't find anything. Moved everything up to the root.

Block Public Access was also still enabled. The AI suggested I replace the existing bucket policy with a fully public `Principal: "*"` one. That was wrong — the bucket already had a correct OAC policy scoped to the CloudFront distribution ARN. The only thing it needed was for Block Public Access to be turned off so the policy could actually be evaluated. Block Public Access overrides bucket policies when it's on, which is easy to miss. Turning it off doesn't make the bucket public — OAC still locks it to CloudFront only.

### CloudFront settings

Two things were missing from the distribution: the alternate domain name (`evanakerly.com`) wasn't set, and the default root object was blank. Without the alternate domain CloudFront rejects requests for the custom domain. Without the default root object it doesn't know to serve `index.html` at `/`. Added both, confirmed the ACM cert for `evanakerly.com` was already attached, and the site came up.

---

## Resources

| Resource | Name / ID |
|---|---|
| S3 Bucket | `evanakerlys-website` (us-east-2) |
| CloudFront Distribution | `E3RZ7XKDIGYTAQ` |
| CloudFront Domain | `d12d4ryy496rqn.cloudfront.net` |
| ACM Certificate | `evanakerly.com` (us-east-1) |
| Cloudflare DNS Record | CNAME `@` → CloudFront domain (DNS only) |

---

## Security Notes

- S3 bucket is private — only CloudFront can read from it via OAC
- OAC uses SigV4 request signing, which is the current best practice over the older Origin Access Identity (OAI) method
- TLS 1.2 minimum enforced via CloudFront security policy (`TLSv1.2_2021`)

---

## Lessons Learned

- Cloudflare Pages shows up as "Worker" in DNS records — to remove a custom domain you go into the Pages project settings, not Workers Routes. Deleting it only removes the mapping, not the domain.
- Always check both record type and proxy status when saving a DNS record in Cloudflare. CloudFront needs a CNAME and DNS Only — both matter.
- Files need to be at the bucket root unless you configure an origin path in CloudFront.
- Block Public Access and bucket policies are separate things. Block Public Access can silently override a valid policy. Turning it off doesn't expose the bucket — your policy still controls access.
- CloudFront certs have to be in us-east-1. Doesn't matter where your bucket is.
- You need both the alternate domain name and the ACM cert set on the distribution before a custom domain works.
- AI assistants get things wrong. Knowing enough to catch it and correct it is part of actually learning the platform.
