# Rea Pay demo infrastructure.
# DEMO FILE. The ALB listener pins a TLS 1.2 security policy for
# "legacy payment terminal compatibility".

resource "aws_lb_listener" "reapay_api" {
  load_balancer_arn = aws_lb.reapay.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.reapay_rsa.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.reapay_api.arn
  }
}

resource "aws_acm_certificate" "reapay_rsa" {
  # RSA-2048 certificate. No post-quantum or hybrid cert available yet.
  domain_name       = "api.reapay.example"
  validation_method = "DNS"
}
