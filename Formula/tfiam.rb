class Tfiam < Formula
  desc "TFIAM - Analyze Terraform repositories and generate IAM permission recommendations with AI explanations"
  homepage "https://github.com/onoureldin14/tfiam"
  url "https://github.com/onoureldin14/tfiam/archive/refs/heads/main.zip"
  version "1.0.0"
  sha256 "ca75c849eb62f065b596a7bd12efb1cf6d346b89ed21537877a46292fa19f7d3"
  license "MIT"

  depends_on "python@3.11"

  def install
    # Install Python dependencies
    system "python3.11", "-m", "pip", "install", "openai>=1.0.0", "pbr>=1.7.5"

    # Copy the entire project to libexec
    libexec.install Dir["*"]

    # Create a wrapper script
    (bin/"tfiam").write <<~EOS
      #!/bin/bash
      exec "#{libexec}/tfiam_standalone.py" "$@"
    EOS

    chmod 0755, bin/"tfiam"
  end

  test do
    system "#{bin}/tfiam", "--help"
  end
end
