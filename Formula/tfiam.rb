class Tfiam < Formula
  desc "TFIAM - Analyze Terraform repositories and generate IAM permission recommendations with AI explanations"
  homepage "https://github.com/onoureldin14/tfiam"
  url "https://github.com/onoureldin14/tfiam/archive/refs/heads/main.zip"
  version "1.0.0"
  sha256 "a3d5a87c768bba6df78fab698d762ae7e9333452decb6d02aa990cf3b5fefe2b"
  license "MIT"

  depends_on "python@3.11"

  def install
    # Install Python dependencies globally
    system "pip3", "install", "openai>=1.0.0", "pbr>=1.7.5"

    # Copy the entire project to libexec
    libexec.install Dir["*"]

    # Create a simple wrapper script
    (bin/"tfiam").write <<~EOS
      #!/bin/bash
      cd "#{libexec}"
      python3 main.py "$@"
    EOS

    chmod 0755, bin/"tfiam"
  end

  test do
    system "#{bin}/tfiam", "--help"
  end
end
